import sys
import os
# fixes an issue keeping pytest from finding project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.lapis.lapis import saveLocation


# Create a mock context with optional attachments
# has fields that fns expect without starting a discord session
def fake_ctx(with_attachment: bool = False):
    ctx = MagicMock()
    ctx.author.id =  id if id is not None else "user123" 
    ctx.author.display_name = "Unrealengine5"
    ctx.send = AsyncMock()
    ctx.message.attachments = [MagicMock()] if with_attachment else []
    return ctx
'''
    All we're testing is the pure behavior of this fn to send data
    regardless of dependency fns it relies on. saveLocation's only independent action is to 
    send data through embeds to the user after they call the command.
'''
@pytest.mark.asyncio
@patch("src.lapis.lapis.makeErrorEmbed")
@patch("src.lapis.lapis.makeEmbed")
@patch("src.lapis.lapis.saveImage", new_callable=AsyncMock)
@patch("src.lapis.lapis.save_location") # save_location -> actual db function
async def test_saveLocation(mock_save_location, mock_saveImage, mock_makeEmbed, mock_makeErrorEmbed):
    # Testing saving location coordinates and name
    ctx = fake_ctx()
    await saveLocation(ctx, "Home", "100 64 200")
    assert mock_save_location.called
    ctx.send.assert_called_once()
    assert "Home has been saved" in mock_makeEmbed.call_args.kwargs["title"]
    
    # Testing coordinate save with an image
    img_ctx = fake_ctx(True)
    await saveLocation(img_ctx, "Castle", "1 4 200")
    assert mock_save_location.called
    mock_saveImage.assert_called_once_with(img_ctx, "Castle")
    img_ctx.send.assert_called_once()
    assert "Castle has been saved" in mock_makeEmbed.call_args.kwargs["title"]
    
    # Testing invalid name/coordinates
    await saveLocation(ctx, "StringBiggerThanThirtyCharacters", "10 10 1")
    assert mock_save_location.called
    assert "Invalid name length. Must between 3 and 30 characters." in mock_makeErrorEmbed.call_args.args[1]
    await saveLocation(ctx, "Regular Name", "invald coordinates")
    assert mock_save_location.called
    assert "Incorrect format. Use double quotes around your numeric coordinates in the form 'X Y Z' or 'X,Y,Z'." in mock_makeErrorEmbed.call_args.args[1]
    



# @pytest.mark.asyncio
# @patch("lapis.lapis.isCorrectNameLength", return_value="Name too long")
# @patch("lapis.lapis.makeErrorEmbed")
# async def test_save_location_bad_name(mock_err_embed, mock_name_len):
#     ctx = fake_ctx()
#     await save_location_cmd(ctx, "BadName", "100 64 200")

#     mock_name_len.assert_called_once()
#     mock_err_embed.assert_called_once()
    # ctx.send.assert_called_once()  # error embed was sent

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


#  pytest -s  tests_lapis.py