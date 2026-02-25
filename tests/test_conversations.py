"""Tests for conversation / note tools."""

import pytest
from freshservice_mcp.server import (
    list_ticket_conversations,
    reply_to_ticket,
    add_ticket_note,
    delete_ticket_note,
)


@pytest.mark.asyncio
async def test_list_ticket_conversations(mock_client):
    await list_ticket_conversations(10)
    mock_client.get.assert_called_once_with(
        "tickets/10/conversations", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_list_ticket_conversations_custom_pagination(mock_client):
    await list_ticket_conversations(10, page=2, per_page=50)
    mock_client.get.assert_called_once_with(
        "tickets/10/conversations", params={"page": 2, "per_page": 50}
    )


@pytest.mark.asyncio
async def test_list_ticket_conversations_caps_per_page(mock_client):
    await list_ticket_conversations(10, per_page=500)
    params = mock_client.get.call_args.kwargs["params"]
    assert params["per_page"] == 100


@pytest.mark.asyncio
async def test_reply_to_ticket_minimal(mock_client):
    await reply_to_ticket(10, body="Hello there")
    mock_client.post.assert_called_once_with(
        "tickets/10/reply", body={"body": "Hello there"}
    )


@pytest.mark.asyncio
async def test_reply_to_ticket_with_cc(mock_client):
    await reply_to_ticket(10, body="Hello", cc_emails=["mgr@example.com"])
    body = mock_client.post.call_args.kwargs["body"]
    assert body["cc_emails"] == ["mgr@example.com"]


@pytest.mark.asyncio
async def test_add_ticket_note_defaults_to_private(mock_client):
    await add_ticket_note(10, body="Internal note")
    mock_client.post.assert_called_once_with(
        "tickets/10/notes", body={"body": "Internal note", "private": True}
    )


@pytest.mark.asyncio
async def test_add_ticket_note_public(mock_client):
    await add_ticket_note(10, body="Public note", private=False)
    body = mock_client.post.call_args.kwargs["body"]
    assert body["private"] is False


@pytest.mark.asyncio
async def test_delete_ticket_note(mock_client):
    result = await delete_ticket_note(10, 999)
    mock_client.delete.assert_called_once_with("tickets/10/conversations/999")
    assert "deleted" in result.lower()
