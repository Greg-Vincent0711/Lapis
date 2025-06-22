import sys
import os
# fixes an issue keeping pytest from finding project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.lapis.lapis import getLocation

@pytest.fixture
def fake_ctx():
    ctx = MagicMock()
    ctx.author.id = "user123"
    ctx.author.display_name = "get_tester"
    ctx.send = AsyncMock()
    return ctx

@pytest.fixture
def common_patches():
    with patch("src.lapis.lapis.makeEmbed") as mock_makeEmbed, \
         patch("src.lapis.lapis.makeErrorEmbed") as mock_makeErrorEmbed, \
         patch("src.lapis.lapis.get_location") as mock_get_location:
        yield {
            "make_embed": mock_makeEmbed,
            "make_errorEmbed": mock_makeErrorEmbed,
            "get_location": mock_get_location,
        }

@pytest.mark.asyncio
async def test_get_success_no_image(fake_ctx, common_patches):
    # we set the return value for get_location(DB fn) since we're purely testing what getLocation does
    common_patches["get_location"].return_value = ["100,64,200"]
    await getLocation(fake_ctx, "Home")
    fake_ctx.send.assert_called_once()
    common_patches["make_embed"].assert_called_once()
    assert "Coordinates for Home" in common_patches["make_embed"].call_args.kwargs["title"]
    assert "100,64,200" in common_patches["make_embed"].call_args.kwargs["description"]

@pytest.mark.asyncio
async def test_get_success_with_image(fake_ctx, common_patches):
    # URL is arbitrary
    common_patches["get_location"].return_value = ["100,64,200", "https://img.url/home.png"]
    await getLocation(fake_ctx, "Home")
    fake_ctx.send.assert_called_once()
    common_patches["make_embed"].assert_called_once()
    assert common_patches["make_embed"].call_args.kwargs["url"] == "https://img.url/home.png"

@pytest.mark.asyncio
async def test_get_invalid_name(fake_ctx, common_patches):
    await getLocation(fake_ctx, "TooLongTooLongTooLong" * 4)
    common_patches["make_errorEmbed"].assert_called_once()
    assert "Invalid name length. Must between 3 and 30 characters." in common_patches["make_errorEmbed"].call_args.args[1]
    fake_ctx.send.assert_called_once()

@pytest.mark.asyncio
async def test_get_location_not_found(fake_ctx, common_patches):
    common_patches["get_location"].return_value = None
    await getLocation(fake_ctx, "Nowhere")
    common_patches["make_errorEmbed"].assert_called_once()
    assert "No location with that name found" in common_patches["make_errorEmbed"].call_args.args[0]
    fake_ctx.send.assert_called_once()

@pytest.mark.asyncio
async def test_get_location_client_error(fake_ctx, common_patches):
    from botocore.exceptions import ClientError
    err = ClientError({"Error": {"Code": "400", "Message": "Boom!"}}, "Query")
    common_patches["get_location"].side_effect = err
    await getLocation(fake_ctx, "Home")
    # should respond with error embed
    common_patches["make_errorEmbed"].assert_called_once()
    fake_ctx.send.assert_called_once()
