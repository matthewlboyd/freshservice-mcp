"""Tests for asset tools."""

import pytest
from freshservice_mcp.server import (
    get_assets,
    get_asset_by_id,
    search_assets,
    filter_assets,
    create_asset,
    update_asset,
    delete_asset,
    get_asset_types,
)


@pytest.mark.asyncio
async def test_get_assets_default(mock_client):
    await get_assets()
    mock_client.get.assert_called_once_with("assets", params={"page": 1, "per_page": 30})


@pytest.mark.asyncio
async def test_get_assets_caps_per_page(mock_client):
    await get_assets(per_page=999)
    params = mock_client.get.call_args.kwargs["params"]
    assert params["per_page"] == 100


@pytest.mark.asyncio
async def test_get_asset_by_id(mock_client):
    await get_asset_by_id(142)
    mock_client.get.assert_called_once_with("assets/142")


@pytest.mark.asyncio
async def test_search_assets(mock_client):
    await search_assets("name:'Dell Laptop'", page=1, per_page=20)
    mock_client.get.assert_called_once_with(
        "assets",
        params={"search": "name:'Dell Laptop'", "page": 1, "per_page": 20},
    )


@pytest.mark.asyncio
async def test_filter_assets_auto_quotes(mock_client):
    await filter_assets("asset_type_id:1")
    params = mock_client.get.call_args.kwargs["params"]
    assert params["query"] == '"asset_type_id:1"'


@pytest.mark.asyncio
async def test_filter_assets_already_quoted(mock_client):
    await filter_assets('"department_id:5"')
    params = mock_client.get.call_args.kwargs["params"]
    assert params["query"] == '"department_id:5"'


@pytest.mark.asyncio
async def test_filter_assets_endpoint(mock_client):
    await filter_assets("asset_type_id:2")
    mock_client.get.assert_called_once_with(
        "assets/filter",
        params={"query": '"asset_type_id:2"', "page": 1, "per_page": 30},
    )


@pytest.mark.asyncio
async def test_create_asset_minimal(mock_client):
    await create_asset(name="ThinkPad X1", asset_type_id=3)
    body = mock_client.post.call_args.kwargs["body"]
    assert body["name"] == "ThinkPad X1"
    assert body["asset_type_id"] == 3
    assert body["impact"] == 1
    assert "description" not in body
    assert "user_id" not in body
    assert "type_fields" not in body


@pytest.mark.asyncio
async def test_create_asset_with_all_optional_fields(mock_client):
    await create_asset(
        name="MacBook Pro",
        asset_type_id=3,
        description="Engineering laptop",
        impact=2,
        user_id=10,
        department_id=4,
        location_id=2,
        agent_id=7,
        asset_tag="ASSET-0042",
        custom_fields={"serial": "SN123"},
    )
    body = mock_client.post.call_args.kwargs["body"]
    assert body["description"] == "Engineering laptop"
    assert body["impact"] == 2
    assert body["user_id"] == 10
    assert body["department_id"] == 4
    assert body["location_id"] == 2
    assert body["agent_id"] == 7
    assert body["asset_tag"] == "ASSET-0042"
    assert body["type_fields"] == {"serial": "SN123"}


@pytest.mark.asyncio
async def test_update_asset(mock_client):
    await update_asset(142, updates={"name": "Renamed Asset"})
    mock_client.put.assert_called_once_with(
        "assets/142", body={"name": "Renamed Asset"}
    )


@pytest.mark.asyncio
async def test_delete_asset(mock_client):
    result = await delete_asset(142)
    mock_client.delete.assert_called_once_with("assets/142")
    assert "142" in result


@pytest.mark.asyncio
async def test_get_asset_types(mock_client):
    await get_asset_types(page=1, per_page=50)
    mock_client.get.assert_called_once_with(
        "asset_types", params={"page": 1, "per_page": 50}
    )
