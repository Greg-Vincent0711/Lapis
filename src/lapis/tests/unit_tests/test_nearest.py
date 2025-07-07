import pytest
from unittest.mock import patch
from src.lapis.lapis import nearest_impl
from testing_utils import mock_interaction

# autospec makes it so that connectToInputHandler mock has the same signature as the actual fn
@pytest.fixture(autouse=True)
def common_patches():
    with patch("src.lapis.backend.seed_impl.format_feature", side_effect=lambda feature: feature.lower()) as mock_format, \
         patch("src.lapis.backend.seed_impl.connectToInputHandler", autospec=True) as mock_connect, \
         patch("src.lapis.backend.seed_impl.makeErrorEmbed", autospec=True) as mock_err, \
         patch("src.lapis.backend.seed_impl.makeEmbed", autospec=True) as mock_embed:
        yield {
            "format_feature": mock_format,
            "connectToInputHandler": mock_connect,
            "makeErrorEmbed": mock_err,
            "makeEmbed": mock_embed
        }


@pytest.mark.asyncio
async def test_nearest_biome_success(common_patches):
    interaction = mock_interaction()
    common_patches["connectToInputHandler"].return_value = {
        "feature": "plains", "x": 123, "z": -456, "error": None
    }
    await nearest_impl(interaction, "Plains", "100", "25", "500")
    # Should defer and send at least 2 messages: searching and success
    interaction.response.defer.assert_awaited_once()
    assert interaction.followup.send.await_count == 2
    expected_args = ["nearest", "plains", "100", "25", "500"]
    common_patches["connectToInputHandler"].assert_called_once_with(interaction.user.id, expected_args)
    
@pytest.mark.asyncio
async def test_nearest_structure_success(common_patches):
    interaction = mock_interaction()
    common_patches["connectToInputHandler"].return_value = {
        "feature": "village", "x": 500, "z": 1000, "error": None
    }

    await nearest_impl(interaction, "Village", "300", "400", "1200")
    expected_args = ["nearest", "village", "300", "400", "1200"]
    common_patches["connectToInputHandler"].assert_called_once_with(interaction.user.id, expected_args)


@pytest.mark.asyncio
async def test_nearest_error_handling(common_patches):
    interaction = mock_interaction()
    common_patches["connectToInputHandler"].return_value = {
        "feature": "village", "x": 0, "z": 0, "error": "Could not find location."
    }
    await nearest_impl(interaction, "Desert", "300", "400", "1200")
    assert "Error" in common_patches["makeErrorEmbed"].call_args[0]






#     interaction = mock_interaction()
#     
#     await nearest_impl(interaction, "Village", "300", "400", "1200")
#     # common_patches["makeErrorEmbed"].assert_called_once()
#     # assert "Error" in common_patches["makeErrorEmbed"].call_args.kwargs["title"]
#     # interaction.followup.send.assert_awaited()
# # assert "Deleted Castle." in common_patches["make_embed"].call_args.kwargs["description"]