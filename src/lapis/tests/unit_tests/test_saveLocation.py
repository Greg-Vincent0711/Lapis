import pytest
from unittest.mock import patch, AsyncMock
from src.lapis.lapis import saveLocation
from src.lapis.api.middleware.errors import InvalidLocationError, LocationLimitExceededError
from src.lapis.helpers.exceptions import S3UploadError
from testing_utils import fake_ctx, AUTHOR_ID

@pytest.fixture
def common_patches():
    with patch("src.lapis.lapis.makeEmbed") as mock_makeEmbed, \
         patch("src.lapis.lapis.storeAttachment", new_callable=AsyncMock) as mock_storeAttachment, \
         patch("src.lapis.lapis.create_location") as mock_create_location, \
         patch("src.lapis.lapis.makeErrorEmbed") as mock_makeErrorEmbed:
        yield {
            "make_embed": mock_makeEmbed,
            "storeAttachment": mock_storeAttachment,
            "create_location": mock_create_location,
            "make_error_embed": mock_makeErrorEmbed,
        }

@pytest.mark.asyncio
async def test_save_success_no_image(common_patches):
    ctx = fake_ctx(with_attachment=False)
    await saveLocation(ctx, "Home", "100 64 200")
    # dimension defaults to Overworld; the service does the validating and formatting
    common_patches["create_location"].assert_called_once_with(AUTHOR_ID, "Home", "Overworld", "100 64 200")
    common_patches["storeAttachment"].assert_not_called()
    ctx.send.assert_called_once()
    assert "Home has been saved" in common_patches["make_embed"].call_args.kwargs["title"]
    assert "100,64,200" in common_patches["make_embed"].call_args.kwargs["description"]

@pytest.mark.asyncio
async def test_save_normalizes_dimension(common_patches):
    ctx = fake_ctx(with_attachment=False)
    await saveLocation(ctx, "Stronghold", "1 4 200", locationType="the end")
    common_patches["create_location"].assert_called_once_with(AUTHOR_ID, "Stronghold", "The End", "1 4 200")

@pytest.mark.asyncio
async def test_save_success_with_image(common_patches):
    ctx = fake_ctx()
    await saveLocation(ctx, "Castle", "1 4 200")
    common_patches["storeAttachment"].assert_awaited_once_with(ctx, "Castle")
    ctx.send.assert_called_once()
    assert "Castle has been saved" in common_patches["make_embed"].call_args.kwargs["title"]

@pytest.mark.asyncio
async def test_save_reports_failed_image_but_keeps_location(common_patches):
    ctx = fake_ctx()
    common_patches["storeAttachment"].side_effect = S3UploadError("S3 failed")
    await saveLocation(ctx, "Castle", "1 4 200")
    common_patches["make_error_embed"].assert_not_called()
    assert "S3 failed" in common_patches["make_embed"].call_args.kwargs["description"]

@pytest.mark.asyncio
@pytest.mark.parametrize("error", [
    InvalidLocationError("Invalid name length. Must between 3 and 30 characters."),
    LocationLimitExceededError("Max 10 locations allowed. Please delete one first."),
])
async def test_save_shows_service_errors(common_patches, error):
    ctx = fake_ctx()
    common_patches["create_location"].side_effect = error
    await saveLocation(ctx, "A" * 40, "10 10 10")
    common_patches["make_error_embed"].assert_called_once()
    assert error.message in common_patches["make_error_embed"].call_args.args[1]
    # nothing else happens once the save itself fails
    common_patches["storeAttachment"].assert_not_called()
    common_patches["make_embed"].assert_not_called()
