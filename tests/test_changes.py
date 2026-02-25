"""Tests for change request tools."""

import pytest
from freshservice_mcp.server import (
    get_changes,
    filter_changes,
    get_change_by_id,
    create_change,
    update_change,
    close_change,
    delete_change,
    get_change_tasks,
    create_change_note,
)


@pytest.mark.asyncio
async def test_get_changes_default(mock_client):
    await get_changes()
    mock_client.get.assert_called_once_with(
        "changes", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_changes_caps_per_page(mock_client):
    await get_changes(per_page=500)
    params = mock_client.get.call_args.kwargs["params"]
    assert params["per_page"] == 100


@pytest.mark.asyncio
async def test_get_changes_with_query_auto_quoted(mock_client):
    await get_changes(query="status:3")
    params = mock_client.get.call_args.kwargs["params"]
    assert params["query"] == '"status:3"'


@pytest.mark.asyncio
async def test_get_changes_with_already_quoted_query(mock_client):
    await get_changes(query='"status:3"')
    params = mock_client.get.call_args.kwargs["params"]
    assert params["query"] == '"status:3"'


@pytest.mark.asyncio
async def test_filter_changes_endpoint(mock_client):
    await filter_changes("approval_status:1", page=1, per_page=20)
    mock_client.get.assert_called_once_with(
        "changes/filter",
        params={"query": '"approval_status:1"', "page": 1, "per_page": 20},
    )


@pytest.mark.asyncio
async def test_filter_changes_auto_quotes(mock_client):
    await filter_changes("status:6")
    params = mock_client.get.call_args.kwargs["params"]
    assert params["query"] == '"status:6"'


@pytest.mark.asyncio
async def test_get_change_by_id(mock_client):
    await get_change_by_id(42)
    mock_client.get.assert_called_once_with("changes/42")


@pytest.mark.asyncio
async def test_create_change_minimal(mock_client):
    await create_change(
        requester_id=1,
        subject="Maintenance window",
        description="Saturday night maintenance",
    )
    body = mock_client.post.call_args.kwargs["body"]
    assert body["requester_id"] == 1
    assert body["subject"] == "Maintenance window"
    assert body["priority"] == 1
    assert body["impact"] == 1
    assert body["status"] == 1
    assert body["risk"] == 1
    assert body["change_type"] == 1
    assert "planned_start_date" not in body
    assert "group_id" not in body


@pytest.mark.asyncio
async def test_create_change_with_dates_and_group(mock_client):
    await create_change(
        requester_id=1,
        subject="DB upgrade",
        description="Upgrade PostgreSQL",
        planned_start_date="2025-03-01T22:00:00Z",
        planned_end_date="2025-03-02T02:00:00Z",
        group_id=5,
        workspace_id=2,
        custom_fields={"cf_risk_assessment": "low"},
    )
    body = mock_client.post.call_args.kwargs["body"]
    assert body["planned_start_date"] == "2025-03-01T22:00:00Z"
    assert body["planned_end_date"] == "2025-03-02T02:00:00Z"
    assert body["group_id"] == 5
    assert body["workspace_id"] == 2
    assert body["custom_fields"] == {"cf_risk_assessment": "low"}


@pytest.mark.asyncio
async def test_update_change(mock_client):
    await update_change(99, change_fields={"status": 3, "priority": 2})
    mock_client.put.assert_called_once_with(
        "changes/99", body={"status": 3, "priority": 2}
    )


@pytest.mark.asyncio
async def test_close_change(mock_client):
    await close_change(77, change_result_explanation="Migration succeeded")
    mock_client.put.assert_called_once_with(
        "changes/77",
        body={
            "status": 6,
            "custom_fields": {"change_result_explanation": "Migration succeeded"},
        },
    )


@pytest.mark.asyncio
async def test_delete_change(mock_client):
    result = await delete_change(33)
    mock_client.delete.assert_called_once_with("changes/33")
    assert "33" in result


@pytest.mark.asyncio
async def test_get_change_tasks(mock_client):
    await get_change_tasks(42)
    mock_client.get.assert_called_once_with("changes/42/tasks")


@pytest.mark.asyncio
async def test_create_change_note_default_private(mock_client):
    await create_change_note(42, body="Note text")
    mock_client.post.assert_called_once_with(
        "changes/42/notes", body={"body": "Note text", "private": True}
    )


@pytest.mark.asyncio
async def test_create_change_note_public(mock_client):
    await create_change_note(42, body="Public note", private=False)
    body = mock_client.post.call_args.kwargs["body"]
    assert body["private"] is False
