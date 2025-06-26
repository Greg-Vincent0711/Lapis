import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

import pytest
from unittest.mock import AsyncMock, patch
from testing_utils import fake_ctx
from src.lapis.lapis import deleteImage

@pytest.fixture(autouse=True)
def common_patches():
    with patch("src.lapis.lapis.isCorrectNameLength", autospec=True) as mock_len, \
         patch("src.lapis.lapis.delete_image_url", new_callable=AsyncMock) as mock_delete, \
         patch("src.lapis.lapis.makeEmbed", autospec=True) as mock_embed, \
         patch("src.lapis.lapis.makeErrorEmbed", autospec=True) as mock_err:
        yield {
            "isCorrectNameLength": mock_len,
            "delete_image_url": mock_delete,
            "makeEmbed": mock_embed,
            "makeErrorEmbed": mock_err,
        }


@pytest.mark.asyncio
async def test_delete_image_success(common_patches):
    ctx = fake_ctx()
    common_patches["isCorrectNameLength"].return_value = True
    common_patches["delete_image_url"].return_value = None 
    
    await deleteImage(ctx, "HomeBase")
    common_patches["delete_image_url"].assert_awaited_once_with(ctx.author.id, "HomeBase")
    common_patches["makeEmbed"].assert_called_once_with(
        "Successful image deletion.",
        "For location HomeBase",
        ctx.author.display_name,
    )
    ctx.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_image_invalid_name(common_patches):
    ctx = fake_ctx()

    # return a validation-error string
    common_patches["isCorrectNameLength"].return_value = "Name too long"

    await deleteImage(ctx, "NameThatIsWayTooLong")
    common_patches["delete_image_url"].assert_not_awaited()
    common_patches["makeErrorEmbed"].assert_called_once_with("Error", "Name too long")
    ctx.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_image_raises(common_patches):
    ctx = fake_ctx()

    common_patches["isCorrectNameLength"].return_value = True
    common_patches["delete_image_url"].side_effect = RuntimeError("DB down")

    await deleteImage(ctx, "HomeBase")

    common_patches["delete_image_url"].assert_awaited_once_with(ctx.author.id, "HomeBase")
    common_patches["makeErrorEmbed"].assert_called_once_with("Error deleting image.", "DB down")
    ctx.send.assert_awaited_once()
