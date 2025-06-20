import sys
import os
# fixes an issue keeping pytest from finding project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.lapis.lapis import saveLocation

@pytest.fixture
def common_patches():
         with patch("src.lapis.lapis.makeEmbed") as mock_makeEmbed, \
            patch("src.lapis.lapis.saveImage", new_callable=AsyncMock) as mock_saveImage, \
            patch("src.lapis.lapis.save_location") as mock_save_location,\
            patch("src.lapis.lapis.makeErrorEmbed") as mock_makeErrorEmbed:
            yield {
                "make_embed": mock_makeEmbed,
                "saveImage": mock_saveImage,
                "save_location": mock_save_location,
                "make_error_embed": mock_makeErrorEmbed
            }


# Create a mock context with optional attachments
# has fields that fns expect without starting a discord session
def fake_ctx(with_attachment: bool = False):
    ctx = MagicMock()
    ctx.author.id =  "user123" 
    ctx.author.display_name = "Unrealengine5"
    ctx.send = AsyncMock()
    ctx.message.attachments = [MagicMock()] if with_attachment else None
    return ctx

@pytest.mark.asyncio
async def test_save_success_no_image(common_patches):
    ctx = fake_ctx()
    await saveLocation(ctx, "Home", "100 64 200")

    # mock_save_location.assert_called_once_with("User123", "Home", "100,64,200")
    common_patches["save_location"].assert_called_once_with("user123", "Home", "100,64,200")
    common_patches["saveImage"].assert_not_called()
    ctx.send.assert_called_once()
    common_patches["make_embed"].assert_called_once()
    assert "Home has been saved" in common_patches["make_embed"].call_args.kwargs["title"]
    

@pytest.mark.asyncio
async def test_save_success_with_image(common_patches):
    # Testing coordinate save with an image
    img_ctx = fake_ctx(True)
    await saveLocation(img_ctx, "Castle", "1 4 200")
    assert common_patches["save_location"].called
    common_patches["saveImage"].assert_called_once_with(img_ctx, "Castle")
    img_ctx.send.assert_called_once()    
    common_patches["make_embed"].assert_called()
    assert "Castle has been saved" in common_patches["make_embed"].call_args.kwargs["title"]
    

@pytest.mark.asyncio
async def test_save_invalid_name(common_patches):
    ctx = fake_ctx()
    await saveLocation(ctx, "A"*40, "10 10 10")
    common_patches["make_error_embed"].assert_called_once()
    assert "Invalid name length" in common_patches["make_error_embed"].call_args.args[1]

@pytest.mark.asyncio
async def test_save_invalid_coords(common_patches):
    ctx = fake_ctx()
    await saveLocation(ctx, "RegularName", "bad coordinates")
    common_patches["make_error_embed"].assert_called_once()
    assert "Incorrect format" in common_patches["make_error_embed"].call_args.args[1]