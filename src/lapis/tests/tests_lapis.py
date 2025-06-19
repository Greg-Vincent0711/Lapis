import sys
import os
# fixes an issue keeping pytest from finding project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.lapis.lapis import saveLocation as save_location_cmd




def fake_ctx(with_attachment: bool = False):
    ctx = MagicMock()
    ctx.author.id = "Not_RealUser123"
    ctx.author.display_name = "Unrealengine5"
    ctx.send = AsyncMock()
    ctx.message.attachments = [MagicMock()] if with_attachment else []
    return ctx

@pytest.mark.asyncio
@patch("lapis.lapis.save_location")
@patch("lapis.lapis.saveImage", new_callable=AsyncMock)
@patch("lapis.lapis.format_coords", return_value="100,64,200")
@patch("lapis.lapis.isCorrectNameLength", return_value=True)
@patch("lapis.lapis.isCorrectCoordFormat", return_value=True)
@patch("lapis.lapis.makeEmbed") # first arg passed to test fn
# all patch dependencies are passed to the fn in order of how theyre called
# fake fns with __ to designate them   
async def test_save_location_success(
    __makeEmbed,
    __coordIsValid,
    __nameIsValid,
    __format,
    __saveImage,
    __saveLocation):
    
    ctx = fake_ctx()
    await save_location_cmd(ctx, "Home", "100 64 200")

    __nameIsValid.assert_called_once_with("Home")
    __coordIsValid.assert_called_once_with("100 64 200")
    __format.assert_called_once_with("100 64 200")
    __saveLocation.assert_called_once_with("user123", "Home", "100,64,200")
    __saveImage.assert_not_called()

    # The embed creation & ctx.send were invoked
    ctx.send.assert_called_once()
    __makeEmbed.assert_called_once()
    assert "Home has been saved." in __makeEmbed.call_args.kwargs["title"]


# @pytest.mark.asyncio
# @patch("lapis.lapis.isCorrectNameLength", return_value="Name too long")
# @patch("lapis.lapis.makeErrorEmbed")
# async def test_save_location_bad_name(mock_err_embed, mock_name_len):
#     ctx = fake_ctx()
#     await save_location_cmd(ctx, "BadName", "100 64 200")

#     mock_name_len.assert_called_once()
#     mock_err_embed.assert_called_once()
#     ctx.send.assert_called_once()  # error embed was sent

# @pytest.mark.asyncio
# @patch("lapis.lapis.isCorrectNameLength", return_value=True)
# @patch("lapis.lapis.isCorrectCoordFormat", return_value="Bad coords")
# @patch("lapis.lapis.makeErrorEmbed")
# async def test_save_location_bad_coords(mock_err_embed, __coordIsValid, __nameIsValid):
#     ctx = fake_ctx()
#     await save_location_cmd(ctx, "Home", "bad coords")

#     __coordIsValid.assert_called_once()
#     mock_err_embed.assert_called_once()
#     ctx.send.assert_called_once()
