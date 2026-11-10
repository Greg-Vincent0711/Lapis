import pytest
from unittest.mock import patch
from src.lapis.lapis import getLocation
from src.lapis.api.middleware.errors import InvalidLocationError, DataAccessError
from testing_utils import fake_ctx, AUTHOR_ID

@pytest.fixture
def common_patches():
    with patch("src.lapis.lapis.makeEmbed") as mock_makeEmbed, \
         patch("src.lapis.lapis.makeErrorEmbed") as mock_makeErrorEmbed, \
         patch("src.lapis.lapis.retrieve_location") as mock_retrieve_location:
        yield {
            "make_embed": mock_makeEmbed,
            "make_errorEmbed": mock_makeErrorEmbed,
            "retrieve_location": mock_retrieve_location,
        }

@pytest.mark.asyncio
async def test_get_success_no_image(common_patches):
    ctx = fake_ctx()
    # we set the return value for the service since we're purely testing what getLocation does with it
    common_patches["retrieve_location"].return_value = {"Coordinates": "100,64,200", "Type": "Nether"}
    await getLocation(ctx, "Home")
    common_patches["retrieve_location"].assert_called_once_with(AUTHOR_ID, "Home")
    ctx.send.assert_called_once()
    kwargs = common_patches["make_embed"].call_args.kwargs
    assert "Coordinates for Home" in kwargs["title"]
    assert "100,64,200" in kwargs["description"] and "Nether" in kwargs["description"]
    assert kwargs["url"] is None

@pytest.mark.asyncio
async def test_get_success_with_image(common_patches):
    ctx = fake_ctx()
    # URL is arbitrary
    common_patches["retrieve_location"].return_value = {"Coordinates": "100,64,200", "Image_URL": "https://img.url/home.png"}
    await getLocation(ctx, "Home")
    ctx.send.assert_called_once()
    assert common_patches["make_embed"].call_args.kwargs["url"] == "https://img.url/home.png"

@pytest.mark.asyncio
async def test_get_location_not_found(common_patches):
    ctx = fake_ctx()
    common_patches["retrieve_location"].side_effect = InvalidLocationError("Location 'Nowhere' not found.")
    await getLocation(ctx, "Nowhere")
    common_patches["make_errorEmbed"].assert_called_once()
    assert "No location with that name found" in common_patches["make_errorEmbed"].call_args.args[0]
    ctx.send.assert_called_once()

@pytest.mark.asyncio
async def test_get_location_database_error(common_patches):
    ctx = fake_ctx()
    common_patches["retrieve_location"].side_effect = DataAccessError("ClientError while fetching location. Try again.")
    await getLocation(ctx, "Home")
    # should respond with error embed
    common_patches["make_errorEmbed"].assert_called_once()
    assert "try again later" in common_patches["make_errorEmbed"].call_args.args[0]
    common_patches["make_embed"].assert_not_called()
    ctx.send.assert_called_once()
