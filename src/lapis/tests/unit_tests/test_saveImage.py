import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.lapis.lapis import InvalidImageFormatError, ImageDownloadError, S3UploadError
from src.lapis.lapis import saveImage
from testing_utils import fake_ctx

@pytest.fixture
def common_patches():
    with patch("src.lapis.lapis.makeErrorEmbed") as mock_makeErrorEmbed, \
         patch("src.lapis.lapis.save_image_url", new_callable=AsyncMock) as mock_save_image_url, \
         patch("src.lapis.lapis.makeEmbed") as mock_makeEmbed:
            yield {
                "makeErrorEmbed": mock_makeErrorEmbed,
                "save_image_url": mock_save_image_url,
                "makeEmbed": mock_makeEmbed
            }
            

@pytest.mark.asyncio
async def test_save_image_invalid_name(common_patches):
    ctx = fake_ctx()
    await saveImage(ctx, "A")
    common_patches["makeErrorEmbed"].assert_called_once_with("Error", "Invalid name length. Must between 3 and 30 characters.")
    ctx.send.assert_called_once()


@pytest.mark.asyncio
async def test_save_image_from_bot_ignored(common_patches):
    ctx = fake_ctx(is_bot=True)
    await saveImage(ctx, "HomeBase")
    common_patches["makeErrorEmbed"].assert_called_once_with("Error", "Ignoring message from bot.")
    ctx.send.assert_called_once()


@pytest.mark.asyncio
async def test_save_image_success(common_patches):
    ctx = fake_ctx()
    common_patches["save_image_url"].return_value = "Saved an image URL for your location."
    await saveImage(ctx, "NetherBase")
    common_patches["save_image_url"].assert_awaited_once_with(ctx.author.id, "NetherBase", ctx.message)
    common_patches["makeEmbed"].assert_called_once_with(title="Success!", description="Saved an image URL for your location.")
    ctx.send.assert_called_once()


@pytest.mark.asyncio
async def test_save_image_db_fail(common_patches):
    ctx = fake_ctx()
    common_patches["save_image_url"].return_value = None
    await saveImage(ctx, "HomeBase")
    common_patches["makeErrorEmbed"].assert_called_once_with("Image not saved", "Failed to update the database. Try again later.")
    ctx.send.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("exception", [ValueError("Bad value"), InvalidImageFormatError("Bad format"),
                                       ImageDownloadError("Download failed"), S3UploadError("S3 failed")])
async def test_save_image_exceptions(common_patches, exception):
    ctx = fake_ctx()
    common_patches["save_image_url"].side_effect = exception
    await saveImage(ctx, "HomeBase")
    common_patches["makeErrorEmbed"].assert_called_once_with("Error saving your image.", str(exception))
    ctx.send.assert_called_once()