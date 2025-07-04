import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import pytest
from unittest.mock import patch
from botocore.exceptions import ClientError
from src.lapis.lapis import list_locations_for_player
from testing_utils import fake_ctx

@pytest.fixture
def common_patches():
    with (
        patch("src.lapis.lapis.list_locations") as mock_list,
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
    common_patches["list"].return_value = "A — 0,0,0"
    await list_locations_for_player(ctx)     
    ctx.send.assert_called_once()
    common_patches["paginate"].assert_not_called
    common_patches["make_embed"].assert_called_once


@pytest.mark.asyncio
async def test_list_paginated(common_patches):
    ctx = fake_ctx()
    # 5 > LOCATIONS_PER_PAGE=3
    locations_string = "\n".join([f"Loc{i} — {i},{i},{i}" for i in range(5)])
    common_patches["list"].return_value = locations_string
    # paginate should return a list[Embed]; we return dummy embeds
    common_patches["paginate"].return_value = ["Embed0", "Embed1"]
    await list_locations_for_player(ctx)
    # paginate takes a list of items, amount per page, boolean to determine format
    common_patches["paginate"].assert_called_once_with(locations_string.split("\n"), 3, False)
    ctx.send.assert_called_once_with(embed="Embed0", view="PaginatorView")


@pytest.mark.asyncio
async def test_list_none(common_patches):
    ctx = fake_ctx()
    common_patches["list"].return_value = ""
    await list_locations_for_player(ctx)
    common_patches["make_error"].assert_called_once_with("You have no locations to list.")
    ctx.send.assert_called_once()


@pytest.mark.asyncio
async def test_list_client_error(common_patches):
    ctx = fake_ctx()
    common_patches["list"].side_effect = ClientError(
        error_response={"Error": {"Message": "Boom!"}}, operation_name="Query"
    )
    await list_locations_for_player(ctx)
    common_patches["make_error"].assert_called_once()
    ctx.send.assert_called_once()
