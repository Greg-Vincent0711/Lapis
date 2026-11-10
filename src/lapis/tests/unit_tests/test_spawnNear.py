import pytest
from unittest.mock import patch
from src.lapis.api.seed_impl import spawn_near_impl
from src.lapis.lapis import spawn_near
from testing_utils import mock_interaction

@pytest.fixture
def connect():
    with patch("src.lapis.api.seed_impl.connectToInputHandler", autospec=True) as mock_connect:
        yield mock_connect

def test_spawn_near_success(connect):
    connect.return_value = [
        {"seed": 12345, "spawn": {"x": 100, "z": 200}},
        {"seed": 67890, "spawn": {"x": -50, "z": 75}}
    ]
    result = spawn_near_impl("5", "2", "1500", biome="Plains", structure="Village")
    connect.assert_called_once_with("5", ["spawn_near", 2, "plains", "Village", 1500])
    assert result == {"result": "12345 with spawn 100,200\n67890 with spawn -50,75\n"}

def test_spawn_near_defaults(connect):
    connect.return_value = [{"seed": 99999, "spawn": {"x": 0, "z": 0}}]
    # an unused biome/structure filter must reach the C code as the literal "None"
    spawn_near_impl("5", "1", "1000", biome=None)
    connect.assert_called_once_with("5", ["spawn_near", 1, "None", "None", 1000])

# the C code reports problems under several keys; all of them should surface as an Error
@pytest.mark.parametrize("c_output, expected", [
    ([{"error": "Invalid radius. Must be greater than 0 and no greater than 3000."}], "Invalid radius"),
    ([{"message": "No seeds found."}], "No seeds found."),
    ([], "no results"),
])
def test_spawn_near_errors(connect, c_output, expected):
    connect.return_value = c_output
    result = spawn_near_impl("5", "1", "3001", structure="Village")
    assert expected in result["Error"]

def test_spawn_near_rejects_non_numbers(connect):
    result = spawn_near_impl("5", "lots", "1000", biome="Plains")
    assert "whole numbers" in result["Error"]
    connect.assert_not_called()

@pytest.mark.asyncio
async def test_spawn_near_command(connect):
    interaction = mock_interaction("spn")
    connect.return_value = [{"seed": 12345, "spawn": {"x": 100, "z": 200}}]
    with patch("src.lapis.lapis.makeEmbed") as make_embed:
        await spawn_near.callback(interaction, "1", "1500", "Plains")
    connect.assert_called_once_with("5", ["spawn_near", 1, "plains", "None", 1500])
    make_embed.assert_called_once_with("Found Seeds", "12345 with spawn 100,200\n", "TestUser")
    interaction.followup.send.assert_awaited_once_with(embed=make_embed.return_value)
