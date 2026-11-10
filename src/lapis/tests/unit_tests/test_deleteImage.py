import pytest
from unittest.mock import AsyncMock, patch
from src.lapis.lapis import deleteImage
from src.lapis.api.middleware.errors import NotFoundError
from testing_utils import fake_ctx, AUTHOR_ID

@pytest.fixture(autouse=True)
def common_patches():
    with patch("src.lapis.lapis.delete_image_url_attempt", new_callable=AsyncMock) as mock_delete, \
         patch("src.lapis.lapis.makeEmbed", autospec=True) as mock_embed, \
         patch("src.lapis.lapis.makeErrorEmbed", autospec=True) as mock_err:
        yield {
            "delete_image": mock_delete,
            "makeEmbed": mock_embed,
            "makeErrorEmbed": mock_err,
        }

@pytest.mark.asyncio
async def test_delete_image_success(common_patches):
    ctx = fake_ctx()
    await deleteImage(ctx, "HomeBase")
    common_patches["delete_image"].assert_awaited_once_with(AUTHOR_ID, "HomeBase")
    common_patches["makeEmbed"].assert_called_once_with(
        "Successful image deletion.",
        "For location HomeBase",
        ctx.author.display_name,
    )
    ctx.send.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.parametrize("error", [NotFoundError("No image found for location 'HomeBase'."), RuntimeError("S3 down")])
async def test_delete_image_raises(common_patches, error):
    ctx = fake_ctx()
    common_patches["delete_image"].side_effect = error
    await deleteImage(ctx, "HomeBase")
    common_patches["makeErrorEmbed"].assert_called_once_with("Error deleting image.", str(error))
    common_patches["makeEmbed"].assert_not_called()
    ctx.send.assert_awaited_once()
