"""Tests for ticket tools."""

import json
import pytest
from freshservice_mcp.server import (
    get_tickets,
    get_ticket_by_id,
    create_ticket,
    update_ticket,
    delete_ticket,
    filter_tickets,
    get_ticket_fields,
)


@pytest.mark.asyncio
async def test_get_tickets_default_params(mock_client):
    await get_tickets()
    mock_client.get.assert_called_once_with("tickets", params={"page": 1, "per_page": 30})


@pytest.mark.asyncio
async def test_get_tickets_custom_params(mock_client):
    await get_tickets(page=3, per_page=50)
    mock_client.get.assert_called_once_with("tickets", params={"page": 3, "per_page": 50})


@pytest.mark.asyncio
async def test_get_tickets_caps_per_page_at_100(mock_client):
    await get_tickets(per_page=200)
    mock_client.get.assert_called_once_with("tickets", params={"page": 1, "per_page": 100})


@pytest.mark.asyncio
async def test_get_ticket_by_id(mock_client):
    mock_client.get.return_value = {"ticket": {"id": 42}}
    result = await get_ticket_by_id(42)
    mock_client.get.assert_called_once_with(
        "tickets/42", params={"include": "conversations,stats,requester"}
    )
    assert "42" in result


@pytest.mark.asyncio
async def test_create_ticket_minimal(mock_client):
    mock_client.post.return_value = {"ticket": {"id": 1}}
    await create_ticket(
        subject="Test ticket",
        description="A test",
        email="user@example.com",
    )
    body = mock_client.post.call_args.kwargs["body"]
    assert body["subject"] == "Test ticket"
    assert body["email"] == "user@example.com"
    assert body["priority"] == 1
    assert body["status"] == 2
    assert body["type"] == "Incident"
    # Optional fields should not be present
    assert "group_id" not in body
    assert "tags" not in body


@pytest.mark.asyncio
async def test_create_ticket_with_optional_fields(mock_client):
    await create_ticket(
        subject="VPN issue",
        description="Can't connect",
        email="user@example.com",
        priority=3,
        status=2,
        group_id=10,
        responder_id=5,
        department_id=7,
        category="Network",
        sub_category="VPN",
        tags=["vpn", "network"],
        cc_emails=["cc@example.com"],
        custom_fields={"cf_env": "prod"},
        workspace_id=2,
    )
    body = mock_client.post.call_args.kwargs["body"]
    assert body["group_id"] == 10
    assert body["responder_id"] == 5
    assert body["department_id"] == 7
    assert body["category"] == "Network"
    assert body["sub_category"] == "VPN"
    assert body["tags"] == ["vpn", "network"]
    assert body["cc_emails"] == ["cc@example.com"]
    assert body["custom_fields"] == {"cf_env": "prod"}
    assert body["workspace_id"] == 2


@pytest.mark.asyncio
async def test_update_ticket(mock_client):
    await update_ticket(99, updates={"status": 4, "priority": 2})
    mock_client.put.assert_called_once_with(
        "tickets/99", body={"status": 4, "priority": 2}
    )


@pytest.mark.asyncio
async def test_delete_ticket(mock_client):
    result = await delete_ticket(55)
    mock_client.delete.assert_called_once_with("tickets/55")
    assert "55" in result


@pytest.mark.asyncio
async def test_filter_tickets_auto_quotes_query(mock_client):
    await filter_tickets("status:2")
    params = mock_client.get.call_args.kwargs["params"]
    assert params["query"] == '"status:2"'


@pytest.mark.asyncio
async def test_filter_tickets_already_quoted_not_double_quoted(mock_client):
    await filter_tickets('"status:2"')
    params = mock_client.get.call_args.kwargs["params"]
    assert params["query"] == '"status:2"'


@pytest.mark.asyncio
async def test_filter_tickets_endpoint(mock_client):
    await filter_tickets("priority:4", page=2, per_page=10)
    mock_client.get.assert_called_once_with(
        "tickets/filter",
        params={"query": '"priority:4"', "page": 2, "per_page": 10},
    )


@pytest.mark.asyncio
async def test_filter_tickets_caps_per_page(mock_client):
    await filter_tickets("status:2", per_page=999)
    params = mock_client.get.call_args.kwargs["params"]
    assert params["per_page"] == 100


@pytest.mark.asyncio
async def test_get_ticket_fields(mock_client):
    await get_ticket_fields()
    mock_client.get.assert_called_once_with("ticket_form_fields")
