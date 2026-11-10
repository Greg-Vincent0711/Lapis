'''
Tests for the business logic layer (db_services.py) that both the bot and the API call.
The repository layer (DynamoDB) is mocked, and "encryption" is replaced with a stand-in
so values stay readable: a stored value is just the text itself.
'''
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.lapis.api.services.db import db_services
from src.lapis.api.middleware.errors import *
from src.lapis.helpers import utils
from src.lapis.api import subprocess as seed_bridge

AUTHOR = "123"

@pytest.fixture(autouse=True)
def fakes():
    fake_decrypt = lambda value: value.encode()
    with patch.object(db_services, "db") as db, \
         patch.object(db_services, "decrypt", side_effect=fake_decrypt), \
         patch.object(utils, "decrypt", side_effect=fake_decrypt), \
         patch.object(db_services, "storeImageInS3", new_callable=AsyncMock) as store, \
         patch.object(db_services, "deleteImage", new_callable=AsyncMock) as delete_async, \
         patch.object(db_services, "deleteImageObject") as delete_object:
        db.get_location_count.return_value = 0
        yield {"db": db, "store": store, "deleteImage": delete_async, "deleteImageObject": delete_object}

# ---------- locations ----------
def test_create_location_stores_normalized_coords(fakes):
    result = db_services.create_location(AUTHOR, "Home", "Overworld", " 10, 64 ,200 ")
    fakes["db"].save_location.assert_called_once_with(AUTHOR, "Home", "Overworld", "10,64,200")
    assert result == {"location_name": "Home", "remaining_locations": 9}

@pytest.mark.parametrize("name, kind, coords, error", [
    ("Home", "Overworld", "10 64 200", UnauthorizedError),      # no author id (see below)
    ("A", "Overworld", "10 64 200", ValidationError),      # name too short
    ("Home", "Overworld", "10 9999 200", ValidationError), # y out of bounds
    ("Home", "Overworld", "ten 64 200", ValidationError),  # not numbers
    ("Home", "Moon", "10 64 200", ValidationError),        # unknown dimension
    ("", "Overworld", "10 64 200", ValidationError),
])
def test_create_location_rejects_bad_input(fakes, name, kind, coords, error):
    author = None if error is UnauthorizedError else AUTHOR
    with pytest.raises(error):
        db_services.create_location(author, name, kind, coords)
    fakes["db"].save_location.assert_not_called()

def test_create_location_enforces_limit(fakes):
    fakes["db"].get_location_count.return_value = 10
    with pytest.raises(LocationLimitExceededError):
        db_services.create_location(AUTHOR, "Home", "Overworld", "10 64 200")
    fakes["db"].save_location.assert_not_called()

def test_retrieve_location_returns_plain_values(fakes):
    fakes["db"].get_location.return_value = {"Item": {"Coordinates": "1,2,3", "Location Type": "Nether", "Image_URL": "https://img"}}
    assert db_services.retrieve_location(AUTHOR, "Home") == {"Coordinates": "1,2,3", "Type": "Nether", "Image_URL": "https://img"}

def test_retrieve_location_not_found(fakes):
    fakes["db"].get_location.return_value = {}
    with pytest.raises(InvalidLocationError):
        db_services.retrieve_location(AUTHOR, "Nowhere")

def test_retrieve_locations_skips_profile_and_seed_rows(fakes):
    fakes["db"].list_locations.return_value = {"Items": [
        {"Location": "hash-of-profile", "cognito_user_id": "abc"},
        {"Location": "SEED", "World_Seed": "42"},
        {"Location_Name": "Home", "Coordinates": "1,2,3", "Location Type": "Nether"},
        # saved before dimensions existed
        {"Location_Name": "Old Base", "Coordinates": "4,5,6"},
    ]}
    assert db_services.retrieve_locations(AUTHOR) == [
        {"Location_Name": "Home", "Coordinates": "1,2,3", "Type": "Nether"},
        {"Location_Name": "Old Base", "Coordinates": "4,5,6", "Type": "Overworld"},
    ]

def test_retrieve_locations_none_saved(fakes):
    fakes["db"].list_locations.return_value = {"Items": [{"Location": "SEED", "World_Seed": "42"}]}
    with pytest.raises(NotFoundError):
        db_services.retrieve_locations(AUTHOR)

def test_update_validates_and_returns_saved_coords(fakes):
    fakes["db"].update_location.return_value = {"Attributes": {"Coordinates": "7,8,9"}}
    assert db_services.create_location_update(AUTHOR, "Home", "7 8 9") == "7,8,9"
    fakes["db"].update_location.assert_called_once_with(AUTHOR, "Home", "7,8,9")
    with pytest.raises(ValidationError):
        db_services.create_location_update(AUTHOR, "Home", "not coords")

def test_delete_location_also_removes_its_image(fakes):
    fakes["db"].delete_location.return_value = {"Attributes": {"Coordinates": "1,2,3", "Image_URL": "https://bucket.s3.amazonaws.com/uploads/a.png"}}
    assert "Successfully deleted" in db_services.delete_location_attempt(AUTHOR, "Home")
    fakes["deleteImageObject"].assert_called_once_with("https://bucket.s3.amazonaws.com/uploads/a.png")

def test_delete_location_not_found(fakes):
    fakes["db"].delete_location.return_value = {}
    with pytest.raises(NotFoundError):
        db_services.delete_location_attempt(AUTHOR, "Nowhere")

# ---------- seeds ----------
def test_set_seed_reaches_the_repository(fakes):
    # this used to call itself forever: the service and repository functions share a name
    fakes["db"].set_seed.return_value = {"Attributes": {"World_Seed": "encrypted"}}
    assert db_services.set_seed(AUTHOR, "12345") == {"msg": "Successfully set world seed."}
    fakes["db"].set_seed.assert_called_once_with(AUTHOR, "12345")

def test_set_seed_converts_text_to_a_number(fakes):
    fakes["db"].set_seed.return_value = {"Attributes": {"World_Seed": "encrypted"}}
    db_services.set_seed(AUTHOR, "my cool world")
    stored = fakes["db"].set_seed.call_args.args[1]
    assert stored.lstrip("-").isdigit()

def test_retrieve_seed(fakes):
    fakes["db"].get_seed.return_value = {"Item": {"World_Seed": "42"}}
    assert db_services.retrieve_seed(AUTHOR) == "42"
    fakes["db"].get_seed.return_value = {}
    with pytest.raises(NotFoundError):
        db_services.retrieve_seed(AUTHOR)

def test_seed_tools_get_the_decrypted_seed(fakes):
    # the C program must be handed the seed itself, not a DynamoDB response
    fakes["db"].get_seed.return_value = {"Item": {"World_Seed": "42"}}
    completed = MagicMock(stdout='{"feature": "Village", "x": 1, "z": 2}\n')
    with patch.object(seed_bridge.subprocess, "run", return_value=completed) as run, \
         patch.dict("os.environ", {"EXECUTABLE_NAME": "./inputHandler"}):
        result = seed_bridge.connectToInputHandler(AUTHOR, ["nearest", "Village", "0", "0", 100])
    assert run.call_args.args[0] == ["./inputHandler", "42", "nearest", "Village", "0", "0", "100"]
    assert result == [{"feature": "Village", "x": 1, "z": 2}]

def test_seed_tools_ignore_text_printed_before_the_json(fakes):
    fakes["db"].get_seed.return_value = {"Item": {"World_Seed": "42"}}
    completed = MagicMock(stdout='Couldn\'t find correct a location.[\n{"seed": 7, "spawn": {"x": 1, "z": 2}}\n]\n')
    with patch.object(seed_bridge.subprocess, "run", return_value=completed), \
         patch.dict("os.environ", {"EXECUTABLE_NAME": "./inputHandler"}):
        assert seed_bridge.connectToInputHandler(AUTHOR, ["spawn_near", 1, "None", "Village", 500]) == [{"seed": 7, "spawn": {"x": 1, "z": 2}}]

# ---------- images ----------
@pytest.mark.asyncio
async def test_create_image_uploads_then_saves_url(fakes):
    fakes["db"].get_location.return_value = {"Item": {"Coordinates": "1,2,3"}}
    fakes["store"].return_value = "https://bucket.s3.amazonaws.com/uploads/123/a.png"
    fakes["db"].save_image_url.return_value = {"Attributes": {"Image_URL": "encrypted"}}
    image = MagicMock()
    result = await db_services.create_image(AUTHOR, "Home", image)
    fakes["store"].assert_awaited_once_with(image, AUTHOR)
    fakes["db"].save_image_url.assert_called_once_with(AUTHOR, "Home", "https://bucket.s3.amazonaws.com/uploads/123/a.png")
    assert result["imageUrl"] == "https://bucket.s3.amazonaws.com/uploads/123/a.png"

@pytest.mark.asyncio
async def test_create_image_for_missing_location_uploads_nothing(fakes):
    fakes["db"].get_location.return_value = {}
    with pytest.raises(InvalidLocationError):
        await db_services.create_image(AUTHOR, "Nowhere", MagicMock())
    fakes["store"].assert_not_called()

@pytest.mark.asyncio
async def test_delete_image_removes_url_and_file(fakes):
    fakes["db"].delete_image_url.return_value = {"Attributes": {"Image_URL": "https://bucket.s3.amazonaws.com/uploads/a.png"}}
    assert "Deleted image" in await db_services.delete_image_url_attempt(AUTHOR, "Home")
    fakes["deleteImage"].assert_awaited_once_with("https://bucket.s3.amazonaws.com/uploads/a.png")

# ---------- helpers ----------
@pytest.mark.parametrize("typed, sent_to_c", [
    ("Desert Pyramid", "Desert_Pyramid"),
    ("desert-pyramid", "Desert_Pyramid"),
    ("Ruined Portal_N", "Ruined_Portal_N"),
    ("Frozen Ocean", "frozen_ocean"),
    ("plains", "plains"),
    ("None", "None"),
    (None, "None"),
])
def test_format_feature(typed, sent_to_c):
    assert utils.format_feature(typed) == sent_to_c


# ---------- Discord linking ----------
import requests as _requests
from src.lapis.api.services.oauth import oauth_services
from src.lapis.api.models.http_models import APIRequest
from src.lapis.api.middleware.errors import ForbiddenError as _Forbidden, UnauthorizedError as _Unauthorized

def _linking_request():
    return APIRequest(method="GET", path="/locations", cognito_user_id="cognito-abc")

def test_unlinked_user_without_a_code_is_forbidden():
    with patch.object(oauth_services, "get_table"), patch.object(oauth_services, "get_credentials", return_value=[]):
        with pytest.raises(_Forbidden):
            oauth_services.get_credentials_attempt(_linking_request())

def test_a_rejected_discord_code_is_unauthorized_not_a_crash():
    with patch.object(oauth_services, "get_table"), patch.object(oauth_services, "get_credentials", return_value=[]), \
         patch.object(oauth_services, "retrieveAccessToken", side_effect=_requests.exceptions.HTTPError("400 invalid_grant")):
        with pytest.raises(_Unauthorized):
            oauth_services.get_credentials_attempt(_linking_request(), "bad-code")

def test_linked_user_gets_their_discord_id():
    with patch.object(oauth_services, "get_table"), patch.object(oauth_services, "get_credentials", return_value=[{"Author_ID": "729"}]):
        assert oauth_services.get_credentials_attempt(_linking_request()) == "729"


# ---------- text seeds match Minecraft Java Edition ----------
from src.lapis.helpers.utils import to_minecraft_seed

# expected values were produced by running String.hashCode() in Java itself
@pytest.mark.parametrize("typed, minecraft_uses", [
    ("hello", "99162322"),
    ("glacier", "108181935"),
    ("Lapis World", "1007338359"),
    ("café", "3045921"),
    ("🙂seed", "991396246"),                  # outside the basic plane: Java hashes two UTF-16 units
    ("99999999999999999999", "1260560192"),  # too big for a long, so Minecraft hashes it as text
    ("  12345 ", "12345"),
    ("-4530634556500121041", "-4530634556500121041"),
])
def test_text_seeds_become_the_same_number_minecraft_uses(typed, minecraft_uses):
    assert to_minecraft_seed(typed) == minecraft_uses
    # converting again changes nothing, so it's safe to apply when reading too
    assert to_minecraft_seed(minecraft_uses) == minecraft_uses

def test_seed_tools_convert_old_text_seeds_when_reading():
    from src.lapis.api import subprocess as seed_runner
    with patch.object(seed_runner, "retrieve_seed", return_value="glacier"), \
         patch.object(seed_runner.subprocess, "run") as run, \
         patch.dict("os.environ", {"EXECUTABLE_NAME": "/bin/inputHandler"}):
        run.return_value = MagicMock(stdout='{"ok": true}', returncode=0)
        seed_runner.connectToInputHandler("123", ["nearest", "plains", "0", "64", "0", "500"])
    assert run.call_args.args[0][:2] == ["/bin/inputHandler", "108181935"]
