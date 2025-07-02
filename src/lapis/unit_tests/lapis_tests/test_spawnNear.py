import pytest
from unittest.mock import patch
from src.lapis.lapis import spawn_near_impl
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
async def test_spawn_near_success(common_patches):
    interaction = mock_interaction()
    common_patches["connectToInputHandler"].return_value = {
    "error": None,
        "seeds": [
            {"seed": 12345, "spawn": {"x": 100, "z": 200}},
            {"seed": 67890, "spawn": {"x": -50, "z": 75}}
        ]
    }

    await spawn_near_impl(interaction, "2", "1500", biome="Plains", structure="Village")
    common_patches["format_feature"].assert_called_once_with("Plains")
    common_patches["connectToInputHandler"].assert_called_once_with(
        "5", ["spawn-near", "2", "plains", "village", 1500]
    )
    interaction.followup.send.assert_any_await(embed=common_patches["embed"].return_value)

@pytest.mark.asyncio
async def test_spawn_near_error(common_patches):
    interaction = mock_interaction()
    common_patches["connectToInputHandler"].return_value = {
        "error": "Invalid search radius"
    }

    await spawn_near_impl(interaction, "1", "3001", biome="None", structure="Stronghold")

    common_patches["format_feature"].assert_any_call("None")
    common_patches["format_feature"].assert_any_call("Stronghold")

    common_patches["connectToInputHandler"].assert_called_once_with(
        "user-123", ["spawn-near", "1", "none", "stronghold", 3001]
    )

    common_patches["embed"].assert_called_once_with(
        "Error retrieving seeds.", "Invalid search radius", "Tester"
    )
    interaction.followup.send.assert_called_with(embed=common_patches["embed"].return_value)

@pytest.mark.asyncio
async def test_spawn_near_defaults(common_patches):
    interaction = mock_interaction()
    common_patches["connectToInputHandler"].return_value = [
        {"seed": 99999, "spawn": {"x": 0, "z": 0}}
    ]

    await spawn_near_impl(interaction, "1", "1000")  # biome and structure default to "None"

    common_patches["format_feature"].assert_any_call("None")
    common_patches["format_feature"].assert_any_call("None")

    common_patches["connectToInputHandler"].assert_called_once_with(
        "5", ["spawn-near", "1", "none", "none", 1000]
    )

    interaction.followup.send.assert_any_await(embed=common_patches["embed"].return_value)
