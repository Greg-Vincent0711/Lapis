import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.lapis.lapis import deleteLocation

def fake_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.author.id = "U999"
    ctx.author.display_name = "Tester"
    ctx.send = AsyncMock()
    return ctx

@pytest.fixture
def common_patches():
    with (
        patch("src.lapis.lapis.isCorrectNameLength", return_value=True) as mock_name_len,
        patch("src.lapis.lapis.delete_location", new_callable=AsyncMock) as mock_delete,
        patch("src.lapis.lapis.makeEmbed") as mock_make_embed,
        patch("src.lapis.lapis.makeErrorEmbed") as mock_make_err,
    ):
        yield {
            "name_len": mock_name_len,
            "delete_location": mock_delete,
            "make_embed": mock_make_embed,
            "make_error": mock_make_err,
        }


@pytest.mark.asyncio
async def test_delete_success(common_patches):
    ctx = fake_ctx()
    common_patches["delete_location"].return_value = "Deleted Castle."
    await deleteLocation(ctx, "Castle")
    common_patches["delete_location"].assert_awaited_once_with(ctx.author.id, "Castle")
    common_patches["make_embed"].assert_called_once()
    ctx.send.assert_called_once()
    assert "Success" in common_patches["make_embed"].call_args.kwargs["title"]
    assert "Deleted Castle." in common_patches["make_embed"].call_args.kwargs["description"]


@pytest.mark.asyncio
async def test_delete_not_found(common_patches):
    ctx = fake_ctx()
    common_patches["delete_location"].return_value = None
    await deleteLocation(ctx, "GhostTown")
    common_patches["make_error"].assert_called_once()
    assert "No matching location found for 'GhostTown'" in common_patches["make_error"].call_args.args[0]
    ctx.send.assert_called_once()


@pytest.mark.asyncio
async def test_delete_invalid_name_length(common_patches):
    ctx = fake_ctx()
    common_patches["name_len"].return_value = "Name must be 3‑30 characters."

    await deleteLocation(ctx, "X")

    ctx.send.assert_called_once_with("Name must be 3‑30 characters.")
    common_patches["delete_location"].assert_not_called()
    common_patches["make_embed"].assert_not_called()
    common_patches["make_error"].assert_not_called()


@pytest.mark.asyncio
async def test_delete_client_error(common_patches):
    from botocore.exceptions import ClientError
    ctx = fake_ctx()
    common_patches["delete_location"].side_effect = ClientError(
        error_response={"Error": {"Message": "Something went wrong deleting your location."}},
        operation_name="DeleteItem",
    )
    await deleteLocation(ctx, "TownHall_Ten")
    common_patches["make_error"].assert_called_once()
    err_args = common_patches["make_error"].call_args.args
    assert "Error deleting TownHall_Ten." in err_args[0]
    assert "Something went wrong deleting your location." in err_args[1]
    ctx.send.assert_called_once()
