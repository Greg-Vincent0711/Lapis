# # test_nearest_command.py
# import pytest
# from unittest.mock import AsyncMock, MagicMock, patch

# @pytest.fixture
# def mock_interaction():
#     user = MagicMock()
#     user.id = 123456
#     user.name = "TestUser"

#     interaction = MagicMock()
#     interaction.user = user

#     interaction.response.defer = AsyncMock()
#     interaction.followup.send = AsyncMock()
#     interaction.command.name = "nearest"

#     return interaction

# @pytest.fixture(autouse=True)
# def patch_helpers():
#     with patch("your_bot.commands.format_feature", side_effect=lambda feature: feature.lower()) as mock_format, \
#          patch("your_bot.commands.connectToInputHandler", autospec=True) as mock_connect, \
#          patch("your_bot.commands.makeErrorEmbed", autospec=True) as mock_err, \
#          patch("your_bot.commands.makeEmbed", autospec=True) as mock_embed, \
#          patch("your_bot.commands.BIOMES", {"plains", "desert", "savanna"}):
#         yield {
#             "format_feature": mock_format,
#             "connectToInputHandler": mock_connect,
#             "makeErrorEmbed": mock_err,
#             "makeEmbed": mock_embed
#         }

# from your_bot.commands import nearest  # must import *after* patch_helpers fixture

# # ---------------------------------------
# # TEST: biome feature = has Y coordinate
# # ---------------------------------------
# @pytest.mark.asyncio
# async def test_nearest_biome_success(mock_interaction, patch_helpers):
#     patch_helpers["connectToInputHandler"].return_value = {
#         "feature": "plains", "x": 123, "z": -456, "error": None
#     }

#     await nearest(mock_interaction, "Plains", "100", "-200", "500")

#     # Should defer and send at least 2 messages
#     mock_interaction.response.defer.assert_awaited_once()
#     assert mock_interaction.followup.send.await_count == 2

#     # Check arguments passed to input handler (should have Y inserted)
#     expected_args = ["nearest", "plains", "100", 0, "-200", "500"]
#     patch_helpers["connectToInputHandler"].assert_called_once_with(mock_interaction.user.id, expected_args)


# # ---------------------------------------
# # TEST: structure = no Y coord inserted
# # ---------------------------------------
# @pytest.mark.asyncio
# async def test_nearest_structure_success(mock_interaction, patch_helpers):
#     patch_helpers["connectToInputHandler"].return_value = {
#         "feature": "village", "x": 500, "z": 1000, "error": None
#     }

#     await nearest(mock_interaction, "Village", "300", "400", "1200")

#     # No Y value inserted because it's a structure
#     expected_args = ["nearest", "village", "300", "400", "1200"]
#     patch_helpers["connectToInputHandler"].assert_called_once_with(mock_interaction.user.id, expected_args)


# # ---------------------------------------
# # TEST: error from input handler
# # ---------------------------------------
# @pytest.mark.asyncio
# async def test_nearest_error_handling(mock_interaction, patch_helpers):
#     patch_helpers["connectToInputHandler"].return_value = {
#         "feature": None, "x": None, "z": None, "error": "Not found"
#     }

#     await nearest(mock_interaction, "Desert", "0", "0", "300")

#     patch_helpers["makeErrorEmbed"].assert_called_once_with(
#         "Error", "Not found", mock_interaction.user.name
#     )
#     mock_interaction.followup.send.assert_awaited()
