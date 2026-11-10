import pytest
from unittest.mock import patch
from src.lapis.lapis import list_locations_for_player
from src.lapis.api.middleware.errors import NotFoundError, DataAccessError
from testing_utils import fake_ctx, AUTHOR_ID

def locations(count):
    return [{"Location_Name": f"Loc{i}", "Coordinates": f"{i},{i},{i}", "Type": "Overworld"} for i in range(count)]

@pytest.fixture
def common_patches():
    with (
        patch("src.lapis.lapis.retrieve_locations") as mock_list,
        patch("src.lapis.lapis.makeEmbed") as mock_make_embed,
        patch("src.lapis.lapis.makeErrorEmbed") as mock_make_error,
        patch("src.lapis.lapis.paginate") as mock_paginate,
        patch("src.lapis.lapis.Paginator", return_value="PaginatorView") as mock_paginator,
    ):
        yield {
            "list": mock_list,
            "make_embed": mock_make_embed,
            "make_error": mock_make_error,
            "paginate": mock_paginate,
            "paginator": mock_paginator,
        }

@pytest.mark.asyncio
async def test_list_small(common_patches):
    ctx = fake_ctx()
    common_patches["list"].return_value = locations(2)
    await list_locations_for_player(ctx)
    common_patches["list"].assert_called_once_with(AUTHOR_ID)
    ctx.send.assert_called_once()
    common_patches["paginate"].assert_not_called()
    description = common_patches["make_embed"].call_args.kwargs["description"]
    assert description == "Loc0 — 0,0,0 (Overworld)\nLoc1 — 1,1,1 (Overworld)"

@pytest.mark.asyncio
async def test_list_paginated(common_patches):
    ctx = fake_ctx()
    # 5 > LOCATIONS_PER_PAGE=3
    common_patches["list"].return_value = locations(5)
    # paginate should return a list[Embed]; we return dummy embeds
    common_patches["paginate"].return_value = ["Embed0", "Embed1"]
    await list_locations_for_player(ctx)
    # paginate takes a list of items, amount per page, boolean to determine format
    expected_lines = [f"Loc{i} — {i},{i},{i} (Overworld)" for i in range(5)]
    common_patches["paginate"].assert_called_once_with(expected_lines, 3, False)
    ctx.send.assert_called_once_with(embed="Embed0", view="PaginatorView")

@pytest.mark.asyncio
async def test_list_none(common_patches):
    ctx = fake_ctx()
    common_patches["list"].side_effect = NotFoundError("No locations exist for this user.")
    await list_locations_for_player(ctx)
    common_patches["make_error"].assert_called_once_with("You have no locations to list.")
    ctx.send.assert_called_once()

@pytest.mark.asyncio
async def test_list_database_error(common_patches):
    ctx = fake_ctx()
    common_patches["list"].side_effect = DataAccessError("Boom!")
    await list_locations_for_player(ctx)
    common_patches["make_error"].assert_called_once_with("Try this command again later.", "Boom!")
    ctx.send.assert_called_once()
