import pytest
from unittest.mock import patch
from src.lapis.api.seed_impl import nearest_impl, NOT_FOUND_COORD
from src.lapis.api.middleware.errors import NotFoundError
from src.lapis.lapis import nearest
from testing_utils import mock_interaction

# autospec makes it so that connectToInputHandler mock has the same signature as the actual fn
@pytest.fixture
def connect():
    with patch("src.lapis.api.seed_impl.connectToInputHandler", autospec=True) as mock_connect:
        yield mock_connect

def test_nearest_biome_passes_a_height(connect):
    connect.return_value = [{"feature": "frozen_ocean", "x": 123, "z": -456}]
    result = nearest_impl("5", "Frozen Ocean", "100", "25", "500")
    # biomes: nearest <biome> x y z radius, named the way the C lookup table spells them
    connect.assert_called_once_with("5", ["nearest", "frozen_ocean", "100", "64", "25", "500"])
    assert result == {"result": "Found frozen_ocean at (123, -456)"}

def test_nearest_structure_has_no_height(connect):
    connect.return_value = [{"feature": "Desert_Pyramid", "x": 500, "z": 1000}]
    result = nearest_impl("5", "desert pyramid", "300", "400", "1200")
    # structures: nearest <structure> x z radius
    connect.assert_called_once_with("5", ["nearest", "Desert_Pyramid", "300", "400", "1200"])
    assert result == {"result": "Found Desert_Pyramid at (500, 1000)"}

def test_nearest_nothing_in_range(connect):
    connect.return_value = [{"feature": "Village", "x": NOT_FOUND_COORD, "z": NOT_FOUND_COORD}]
    result = nearest_impl("5", "Village", "0", "0", "10")
    assert "No Village found" in result["Error"]

def test_nearest_unknown_feature(connect):
    connect.return_value = [{"Error": "Incorrect usage."}]
    result = nearest_impl("5", "Candy Land", "0", "0", "10")
    assert "Candy Land" in result["Error"]

# the slash command itself: defer, run the search, answer with a follow up
@pytest.mark.asyncio
async def test_nearest_command_success(connect):
    interaction = mock_interaction()
    connect.return_value = [{"feature": "Village", "x": 1, "z": 2}]
    with patch("src.lapis.lapis.makeEmbed") as make_embed:
        await nearest.callback(interaction, "Village", "0", "0", "100")
    interaction.response.defer.assert_awaited_once()
    connect.assert_called_once_with("5", ["nearest", "Village", "0", "0", "100"])
    make_embed.assert_called_once_with("Nearest Village", "Found Village at (1, 2)", "TestUser")
    interaction.followup.send.assert_awaited_once_with(embed=make_embed.return_value)

@pytest.mark.asyncio
async def test_nearest_command_without_a_saved_seed(connect):
    interaction = mock_interaction()
    connect.side_effect = NotFoundError("World seed not found for this user.")
    with patch("src.lapis.lapis.makeErrorEmbed") as make_error:
        await nearest.callback(interaction, "Village", "0", "0", "100")
    make_error.assert_called_once_with("Error", "World seed not found for this user. Set one with !ss.")
    interaction.followup.send.assert_awaited_once_with(embed=make_error.return_value)
