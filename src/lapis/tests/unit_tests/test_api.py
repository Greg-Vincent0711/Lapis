'''
Drives the DB Lambda the way API Gateway does: a raw event goes in, a Lambda response comes out.
Only the outermost edges are mocked (who the caller is, and the DynamoDB repository), so the
routing, handlers and services all run for real.
'''
import json
import pytest
from unittest.mock import patch, AsyncMock
from src.lapis.api import db_lambda, seed_lambda
from src.lapis.api.services.db import db_services
import base64
from src.lapis.api.middleware.errors import UnauthorizedError, NotFoundError, ForbiddenError
from src.lapis.api.handler_methods import upsert_handlers
from src.lapis.helpers import utils

def event(method, path, body=None, query=None):
    return {
        # API Gateway includes the stage name in the path
        "rawPath": f"/prod{path}",
        "requestContext": {"http": {"method": method}, "authorizer": {"jwt": {"claims": {"sub": "cognito-abc"}}}},
        "queryStringParameters": query,
        "body": json.dumps(body) if body is not None else None,
    }

def call(method, path, body=None):
    response = db_lambda.handler(event(method, path, body), None)
    return response["statusCode"], json.loads(response["body"])

@pytest.fixture(autouse=True)
def fakes():
    fake_decrypt = lambda value: value.encode()
    with patch.object(db_lambda, "get_credentials_attempt", return_value="123") as credentials, \
         patch.object(db_services, "db") as db, \
         patch.object(db_services, "decrypt", side_effect=fake_decrypt), \
         patch.object(utils, "decrypt", side_effect=fake_decrypt), \
         patch.object(db_services, "deleteImage", new_callable=AsyncMock) as delete_image:
        db.get_location_count.return_value = 0
        yield {"credentials": credentials, "db": db, "deleteImage": delete_image}

def test_list_locations(fakes):
    fakes["db"].list_locations.return_value = {"Items": [{"Location_Name": "Home", "Coordinates": "1,2,3", "Location Type": "Nether"}]}
    status, body = call("GET", "/locations")
    assert status == 200
    assert body == {"locations": [{"Location_Name": "Home", "Coordinates": "1,2,3", "Type": "Nether"}]}

def test_save_location_in_the_shape_the_website_sends(fakes):
    status, body = call("POST", "/locations", {"id": "abc", "location_name": "Home", "type": "Overworld", "coords": "0, 64, 0"})
    assert status == 201
    fakes["db"].save_location.assert_called_once_with("123", "Home", "Overworld", "0,64,0")

def test_get_one_location_by_path(fakes):
    fakes["db"].get_location.return_value = {"Item": {"Coordinates": "1,2,3"}}
    status, body = call("GET", "/locations/Home")
    assert (status, body) == (200, {"Coordinates": "1,2,3"})
    fakes["db"].get_location.assert_called_once_with("123", "Home")

def test_update_location_both_ways(fakes):
    fakes["db"].update_location.return_value = {"Attributes": {"Coordinates": "7,8,9"}}
    # the website: PUT /locations with everything in the body
    assert call("PUT", "/locations", {"location_name": "Home", "coords": "7, 8, 9"})[0] == 200
    # by path
    assert call("PUT", "/locations/Home", {"new_coords": "7 8 9"}) == (200, {"message": "Updated 'Home'.", "coords": "7,8,9"})
    assert fakes["db"].update_location.call_args_list[0].args == ("123", "Home", "7,8,9")
    assert fakes["db"].update_location.call_args_list[1].args == ("123", "Home", "7,8,9")

def test_delete_location(fakes):
    fakes["db"].delete_location.return_value = {"Attributes": {"Coordinates": "1,2,3"}}
    assert call("DELETE", "/locations/Home")[0] == 200
    fakes["db"].delete_location.return_value = {}
    assert call("DELETE", "/locations/Nowhere")[0] == 404

def test_delete_image_route_is_async(fakes):
    fakes["db"].delete_image_url.return_value = {"Attributes": {"Image_URL": "https://bucket.s3.amazonaws.com/uploads/a.png"}}
    status, body = call("DELETE", "/locations/Home/img")
    assert status == 200
    fakes["deleteImage"].assert_awaited_once()

def test_seed_round_trip(fakes):
    fakes["db"].set_seed.return_value = {"Attributes": {"World_Seed": "encrypted"}}
    assert call("POST", "/seed", {"seed": "42"}) == (201, {"msg": "Successfully set world seed."})
    fakes["db"].get_seed.return_value = {"Item": {"World_Seed": "42"}}
    assert call("GET", "/seed") == (200, {"seed": "42"})

def test_duplicate_name_is_a_409(fakes):
    from src.lapis.api.middleware.errors import ConflictError
    fakes["db"].save_location.side_effect = ConflictError("A location named 'Home' already exists. Update it or pick another name.")
    status, body = call("POST", "/locations", {"location_name": "Home", "type": "Overworld", "coords": "0 64 0"})
    assert status == 409 and "already exists" in body["error"]

def test_bad_coords_are_a_400(fakes):
    assert call("POST", "/locations", {"location_name": "Home", "type": "Overworld", "coords": "10, 999"})[0] == 400

def test_bad_input_is_a_400_not_a_crash(fakes):
    assert call("POST", "/seed", {})[0] == 400
    assert call("POST", "/locations", {"location_name": "Home"})[0] == 400

def test_unknown_route_is_a_404(fakes):
    status, body = call("GET", "/nope")
    assert status == 404 and "No route" in body["error"]

def test_unlinked_user_is_a_403_not_a_500(fakes):
    # the website shows "Connect to Discord" on exactly this
    fakes["credentials"].side_effect = ForbiddenError("Discord account not linked. Connect Discord first.")
    status, body = call("GET", "/locations")
    assert status == 403 and "not linked" in body["error"]

def test_linked_user_with_no_locations_gets_an_empty_list(fakes):
    fakes["db"].list_locations.return_value = {"Items": []}
    assert call("GET", "/locations") == (200, {"locations": []})

def test_list_includes_the_image(fakes):
    fakes["db"].list_locations.return_value = {"Items": [{"Location_Name": "Home", "Coordinates": "1,2,3", "Image_URL": "https://b.s3.amazonaws.com/uploads/1/a.png"}]}
    assert call("GET", "/locations")[1]["locations"][0]["Image_URL"] == "https://b.s3.amazonaws.com/uploads/1/a.png"

def test_names_with_spaces_are_url_decoded(fakes):
    fakes["db"].get_location.return_value = {"Item": {"Coordinates": "1,2,3"}}
    assert call("GET", "/locations/My%20Base")[0] == 200
    fakes["db"].get_location.assert_called_once_with("123", "My Base")
    fakes["db"].delete_location.return_value = {"Attributes": {"Coordinates": "1,2,3"}}
    assert call("DELETE", "/locations/My%20Base")[0] == 200
    assert fakes["db"].delete_location.call_args.args == ("123", "My Base")

def test_handled_errors_use_the_error_key(fakes):
    fakes["db"].get_location.return_value = {"Item": {}}
    status, body = call("GET", "/locations/Nowhere")
    assert status == 404 and set(body) == {"error"}

PNG = b"\x89PNG\r\n\x1a\nfake"

def test_upload_image_from_the_browser(fakes):
    fakes["db"].get_location.return_value = {"Item": {"Coordinates": "1,2,3"}}
    fakes["db"].save_image_url.return_value = {"Attributes": {"Image_URL": "x"}}
    with patch.object(db_services, "storeImageInS3", new_callable=AsyncMock, return_value="https://b.s3.amazonaws.com/uploads/123/a.png") as store:
        data_url = "data:image/png;base64," + base64.b64encode(PNG).decode()
        status, body = call("PUT", "/locations/My%20Base/img", {"image_base64": data_url})
    assert status == 201 and body["imageUrl"] == "https://b.s3.amazonaws.com/uploads/123/a.png"
    sent = store.await_args.args[0]
    assert (sent.data, sent.content_type) == (PNG, "image/png")
    assert fakes["db"].save_image_url.call_args.args[1] == "My Base"

def test_upload_rejects_bad_or_huge_images(fakes):
    assert call("PUT", "/locations/Home/img", {"image_base64": "not base64!!", "content_type": "image/png"})[0] == 400
    with patch.object(upsert_handlers, "MAX_IMAGE_BYTES", 3):
        status, body = call("PUT", "/locations/Home/img", {"image_base64": base64.b64encode(PNG).decode(), "content_type": "image/png"})
    assert status == 400 and "too large" in body["error"]
    assert call("PUT", "/locations/Home/img", {})[0] == 400

def test_replacing_an_image_deletes_the_old_file(fakes):
    fakes["db"].get_location.return_value = {"Item": {"Coordinates": "1,2,3", "Image_URL": "https://b.s3.amazonaws.com/uploads/123/old.png"}}
    fakes["db"].save_image_url.return_value = {"Attributes": {"Image_URL": "x"}}
    with patch.object(db_services, "storeImageInS3", new_callable=AsyncMock, return_value="https://b.s3.amazonaws.com/uploads/123/new.png"), \
         patch.object(db_services, "deleteImageObject") as delete_old:
        call("PUT", "/locations/Home/img", {"image_base64": base64.b64encode(PNG).decode(), "content_type": "image/png"})
    delete_old.assert_called_once_with("https://b.s3.amazonaws.com/uploads/123/old.png")

def test_linking_discord_returns_200(fakes):
    # /auth/callback skips the credentials lookup in db_lambda and does its own inside the handler
    with patch("src.lapis.api.handler_methods.upsert_handlers.get_credentials_attempt", return_value="123") as link:
        status, body = call("POST", "/auth/callback", {"authCode": "discord-code"})
    assert status == 200
    assert link.call_args.args[1] == "discord-code"
    assert call("POST", "/auth/callback", {})[0] == 400

# ---------- seed Lambda ----------
def seed_call(query):
    response = seed_lambda.handler(event("GET", "/seedInfo", query=query), None)
    return response["statusCode"], json.loads(response["body"])

def test_seed_lambda_nearest():
    with patch("src.lapis.api.seed_impl.connectToInputHandler", return_value=[{"feature": "Village", "x": 1, "z": 2}]) as connect:
        status, body = seed_call({"Author_ID": "123", "requestType": "nearest", "feature": "village", "x_coord": "0", "z_coord": "0", "radius": "100"})
    assert (status, body) == (200, {"result": "Found Village at (1, 2)"})
    connect.assert_called_once_with("123", ["nearest", "Village", "0", "0", "100"])

def test_seed_lambda_spawn_near_with_only_a_biome():
    with patch("src.lapis.api.seed_impl.connectToInputHandler", return_value=[{"seed": 7, "spawn": {"x": 1, "z": 2}}]) as connect:
        status, body = seed_call({"Author_ID": "123", "requestType": "spawn-near", "numseeds": "1", "range_val": "500", "biome": "Plains"})
    assert status == 200
    connect.assert_called_once_with("123", ["spawn_near", 1, "plains", "None", 500])

def test_seed_lambda_without_a_saved_seed_is_a_404():
    with patch("src.lapis.api.seed_impl.connectToInputHandler", side_effect=NotFoundError("World seed not found for this user.")):
        status, body = seed_call({"Author_ID": "123", "requestType": "nearest", "feature": "village", "x_coord": "0", "z_coord": "0", "radius": "100"})
    assert (status, body) == (404, {"Error": "World seed not found for this user."})
