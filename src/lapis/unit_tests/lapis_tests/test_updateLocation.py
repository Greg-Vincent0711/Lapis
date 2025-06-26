import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from botocore.exceptions import ClientError
from src.lapis.lapis import updateLocation
from testing_utils import fake_ctx

@pytest.fixture
def common_patches():
    with (
        patch("src.lapis.lapis.isCorrectNameLength", return_value=True) as mock_name,
        patch("src.lapis.lapis.isCorrectCoordFormat", return_value=True) as mock_coord,
        patch("src.lapis.lapis.update_location") as mock_update,
        patch("src.lapis.lapis.format_coords", return_value="10,64,200") as mock_format,
        patch("src.lapis.lapis.makeEmbed") as mock_embed,
        patch("src.lapis.lapis.makeErrorEmbed") as mock_error_embed,
    ):
        yield {
            "name_check": mock_name,
            "coord_check": mock_coord,
            "update_location": mock_update,
            "format_coords": mock_format,
            "make_embed": mock_embed,
            "make_error_embed": mock_error_embed,
        }


@pytest.mark.asyncio
async def test_update_success(common_patches):
    ctx = fake_ctx()
    common_patches["update_location"].return_value = "10,64,200"
    await updateLocation(ctx, "Castle", "10 64 200")
    common_patches["format_coords"].assert_called_once_with("10 64 200")
    common_patches["update_location"].assert_called_once_with("user123", "Castle", "10,64,200")
    common_patches["make_embed"].assert_called_once()
    ctx.send.assert_called_once()


@pytest.mark.asyncio
async def test_update_invalid_name(common_patches):
    ctx = fake_ctx()
    common_patches["name_check"].return_value = "Invalid name"
    await updateLocation(ctx, "TooLongName" * 5, "10 64 200")
    ctx.send.assert_called_once_with("Invalid name")
    common_patches["update_location"].assert_not_called()
    common_patches["make_embed"].assert_not_called()
    common_patches["make_error_embed"].assert_not_called()


@pytest.mark.asyncio
async def test_update_invalid_coords(common_patches):
    ctx = fake_ctx()
    common_patches["coord_check"].return_value = "Invalid coords"
    await updateLocation(ctx, "Castle", "bad coords")
    ctx.send.assert_called_once_with("Invalid coords")
    common_patches["update_location"].assert_not_called()
    common_patches["make_embed"].assert_not_called()
    common_patches["make_error_embed"].assert_not_called()


@pytest.mark.asyncio
async def test_update_location_not_found(common_patches):
    ctx = fake_ctx()
    common_patches["update_location"].return_value = None
    await updateLocation(ctx, "GhostBase", "10 64 200")
    common_patches["make_error_embed"].assert_called_once_with("Error updating GhostBase")
    ctx.send.assert_called_once()


@pytest.mark.asyncio
async def test_update_client_error(common_patches):
    ctx = fake_ctx()
    common_patches["update_location"].side_effect = ClientError(
        error_response={"Error": {"Message": "DynamoDB failure"}},
        operation_name="UpdateItem"
    )
    await updateLocation(ctx, "NetherFortress", "0 0 0")
    common_patches["make_error_embed"].assert_called_once_with(
        "Error updating NetherFortress", "DynamoDB failure"
    )
    ctx.send.assert_called_once()
