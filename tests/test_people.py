"""Tests for agents, requesters, and group tools."""

import pytest
from freshservice_mcp.server import (
    get_requesters,
    get_requester_by_id,
    filter_requesters,
    create_requester,
    get_agents,
    get_agent_by_id,
    filter_agents,
    get_agent_groups,
    get_agent_group_by_id,
    get_requester_groups,
    get_requester_group_by_id,
)


# ---------------------------------------------------------------------------
# Requesters
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_requesters_default(mock_client):
    await get_requesters()
    mock_client.get.assert_called_once_with(
        "requesters", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_requesters_caps_per_page(mock_client):
    await get_requesters(per_page=999)
    params = mock_client.get.call_args.kwargs["params"]
    assert params["per_page"] == 100


@pytest.mark.asyncio
async def test_get_requester_by_id(mock_client):
    await get_requester_by_id(7)
    mock_client.get.assert_called_once_with("requesters/7")


@pytest.mark.asyncio
async def test_filter_requesters(mock_client):
    await filter_requesters("john@example.com", page=1, per_page=10)
    mock_client.get.assert_called_once_with(
        "requesters",
        params={"query": "john@example.com", "page": 1, "per_page": 10},
    )


@pytest.mark.asyncio
async def test_create_requester_minimal(mock_client):
    await create_requester(first_name="Alice")
    body = mock_client.post.call_args.kwargs["body"]
    assert body["first_name"] == "Alice"
    assert "primary_email" not in body
    assert "last_name" not in body
    assert "phone" not in body


@pytest.mark.asyncio
async def test_create_requester_full(mock_client):
    await create_requester(
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        phone="+1-555-0100",
        department_ids=[3, 5],
        custom_fields={"cf_employee_id": "EMP001"},
    )
    body = mock_client.post.call_args.kwargs["body"]
    assert body["first_name"] == "Alice"
    assert body["last_name"] == "Smith"
    assert body["primary_email"] == "alice@example.com"
    assert body["phone"] == "+1-555-0100"
    assert body["department_ids"] == [3, 5]
    assert body["custom_fields"] == {"cf_employee_id": "EMP001"}


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_agents_default(mock_client):
    await get_agents()
    mock_client.get.assert_called_once_with(
        "agents", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_agents_caps_per_page(mock_client):
    await get_agents(per_page=200)
    params = mock_client.get.call_args.kwargs["params"]
    assert params["per_page"] == 100


@pytest.mark.asyncio
async def test_get_agent_by_id(mock_client):
    await get_agent_by_id(12)
    mock_client.get.assert_called_once_with("agents/12")


@pytest.mark.asyncio
async def test_filter_agents(mock_client):
    await filter_agents("active:true", page=1, per_page=50)
    mock_client.get.assert_called_once_with(
        "agents",
        params={"query": "active:true", "page": 1, "per_page": 50},
    )


# ---------------------------------------------------------------------------
# Agent Groups
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_agent_groups(mock_client):
    await get_agent_groups()
    mock_client.get.assert_called_once_with(
        "groups", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_agent_group_by_id(mock_client):
    await get_agent_group_by_id(3)
    mock_client.get.assert_called_once_with("groups/3")


# ---------------------------------------------------------------------------
# Requester Groups
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_requester_groups(mock_client):
    await get_requester_groups()
    mock_client.get.assert_called_once_with(
        "requester_groups", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_requester_group_by_id(mock_client):
    await get_requester_group_by_id(8)
    mock_client.get.assert_called_once_with("requester_groups/8")
