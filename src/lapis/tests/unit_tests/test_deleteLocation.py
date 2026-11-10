import pytest
from unittest.mock import patch
from src.lapis.lapis import deleteLocation
from src.lapis.api.middleware.errors import NotFoundError, DataAccessError
from testing_utils import fake_ctx, AUTHOR_ID

@pytest.fixture
def common_patches():
    with (
        patch("src.lapis.lapis.delete_location_attempt") as mock_delete,
        patch("src.lapis.lapis.makeEmbed") as mock_make_embed,
        patch("src.lapis.lapis.makeErrorEmbed") as mock_make_err,
    ):
        yield {
            "delete_location": mock_delete,
            "make_embed": mock_make_embed,
            "make_error": mock_make_err,
        }

@pytest.mark.asyncio
async def test_delete_success(common_patches):
    ctx = fake_ctx()
    common_patches["delete_location"].return_value = "Successfully deleted location 'Castle'."
    await deleteLocation(ctx, "Castle")
    common_patches["delete_location"].assert_called_once_with(AUTHOR_ID, "Castle")
    ctx.send.assert_called_once()
    assert "Success" in common_patches["make_embed"].call_args.kwargs["title"]
    assert "Castle" in common_patches["make_embed"].call_args.kwargs["description"]

@pytest.mark.asyncio
async def test_delete_not_found(common_patches):
    ctx = fake_ctx()
    common_patches["delete_location"].side_effect = NotFoundError("Location 'GhostTown' not found.")
    await deleteLocation(ctx, "GhostTown")
    common_patches["make_error"].assert_called_once()
    assert "No matching location found for 'GhostTown'" in common_patches["make_error"].call_args.args[0]
    common_patches["make_embed"].assert_not_called()
    ctx.send.assert_called_once()

@pytest.mark.asyncio
async def test_delete_database_error(common_patches):
    ctx = fake_ctx()
    common_patches["delete_location"].side_effect = DataAccessError("Something went wrong deleting your location.")
    await deleteLocation(ctx, "TownHall_Ten")
    err_args = common_patches["make_error"].call_args.args
    assert "Error deleting TownHall_Ten." in err_args[0]
    assert "Something went wrong deleting your location." in err_args[1]
    ctx.send.assert_called_once()
