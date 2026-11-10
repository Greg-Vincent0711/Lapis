import pytest
from unittest.mock import patch, AsyncMock
from src.lapis.lapis import saveImage
from src.lapis.api.middleware.errors import InvalidLocationError
from src.lapis.helpers.exceptions import InvalidImageFormatError, ImageDownloadError, S3UploadError
from testing_utils import fake_ctx, AUTHOR_ID

@pytest.fixture
def common_patches():
    with patch("src.lapis.lapis.makeErrorEmbed") as mock_makeErrorEmbed, \
         patch("src.lapis.lapis.create_image", new_callable=AsyncMock) as mock_create_image, \
         patch("src.lapis.lapis.makeEmbed") as mock_makeEmbed:
        yield {
            "makeErrorEmbed": mock_makeErrorEmbed,
            "create_image": mock_create_image,
            "makeEmbed": mock_makeEmbed,
        }

@pytest.mark.asyncio
async def test_save_image_from_bot_ignored(common_patches):
    ctx = fake_ctx(is_bot=True)
    await saveImage(ctx, "HomeBase")
    common_patches["makeErrorEmbed"].assert_called_once_with("Error", "Ignoring message from bot.")
    common_patches["create_image"].assert_not_called()
    ctx.send.assert_called_once()

@pytest.mark.asyncio
async def test_save_image_without_attachment(common_patches):
    ctx = fake_ctx(with_attachment=False)
    await saveImage(ctx, "HomeBase")
    common_patches["create_image"].assert_not_called()
    assert "Attach" in common_patches["makeErrorEmbed"].call_args.args[1]
    ctx.send.assert_called_once()

@pytest.mark.asyncio
async def test_save_image_success(common_patches):
    ctx = fake_ctx()
    common_patches["create_image"].return_value = {"msg": "Saved.", "imageUrl": "https://bucket.s3.amazonaws.com/uploads/123/a.png"}
    await saveImage(ctx, "NetherBase")
    # the attachment itself is handed over, not the whole Discord message
    common_patches["create_image"].assert_awaited_once_with(AUTHOR_ID, "NetherBase", ctx.message.attachments[0])
    kwargs = common_patches["makeEmbed"].call_args.kwargs
    assert kwargs["title"] == "Success!"
    assert kwargs["url"] == "https://bucket.s3.amazonaws.com/uploads/123/a.png"
    ctx.send.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.parametrize("exception", [ValueError("Bad value"), InvalidImageFormatError("Bad format"),
                                       ImageDownloadError("Download failed"), S3UploadError("S3 failed"),
                                       InvalidLocationError("Location 'HomeBase' not found.")])
async def test_save_image_exceptions(common_patches, exception):
    ctx = fake_ctx()
    common_patches["create_image"].side_effect = exception
    await saveImage(ctx, "HomeBase")
    common_patches["makeErrorEmbed"].assert_called_once_with("Error saving your image.", str(exception))
    ctx.send.assert_called_once()
