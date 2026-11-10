import pytest
from unittest.mock import patch
from src.lapis.lapis import updateLocation
from src.lapis.api.middleware.errors import ValidationError, InvalidLocationError
from testing_utils import fake_ctx, AUTHOR_ID

@pytest.fixture
def common_patches():
    with (
        patch("src.lapis.lapis.create_location_update") as mock_update,
        patch("src.lapis.lapis.makeEmbed") as mock_embed,
        patch("src.lapis.lapis.makeErrorEmbed") as mock_error_embed,
    ):
        yield {
            "update_location": mock_update,
            "make_embed": mock_embed,
            "make_error_embed": mock_error_embed,
        }

@pytest.mark.asyncio
async def test_update_success(common_patches):
    ctx = fake_ctx()
    common_patches["update_location"].return_value = "10,64,200"
    await updateLocation(ctx, "Castle", "10 64 200")
    common_patches["update_location"].assert_called_once_with(AUTHOR_ID, "Castle", "10 64 200")
    assert "10,64,200" in common_patches["make_embed"].call_args.kwargs["description"]
    ctx.send.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.parametrize("error", [
    ValidationError("Incorrect format."),
    InvalidLocationError("Location 'GhostBase' not found."),
])
async def test_update_shows_service_errors(common_patches, error):
    ctx = fake_ctx()
    common_patches["update_location"].side_effect = error
    await updateLocation(ctx, "GhostBase", "10 64 200")
    common_patches["make_error_embed"].assert_called_once_with("Error updating GhostBase", error.message)
    common_patches["make_embed"].assert_not_called()
    ctx.send.assert_called_once()
