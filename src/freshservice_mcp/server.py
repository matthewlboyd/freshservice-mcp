"""Freshservice MCP Server — a local MCP server for Freshservice ITSM operations.

Supports: Tickets, Changes, Conversations, Assets, Agents, Requesters,
Agent Groups, Requester Groups, Products, Canned Responses, Workspaces,
Solution Categories, Solution Folders, Solution Articles.
"""

from __future__ import annotations

import json
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from freshservice_mcp.client import FreshserviceClient, FreshserviceAPIError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan — create/destroy the API client
# ---------------------------------------------------------------------------

_client: FreshserviceClient | None = None


@asynccontextmanager
async def lifespan(server: FastMCP):
    global _client
    try:
        _client = FreshserviceClient()
        logger.info(f"Connected to Freshservice: {_client.domain}")
        yield
    finally:
        if _client:
            await _client.close()
            _client = None


mcp = FastMCP(
    "Freshservice MCP Server",
    instructions="MCP server for Freshservice ITSM — manage tickets, changes, assets, and more.",
    lifespan=lifespan,
)


def _client_or_error() -> FreshserviceClient:
    if _client is None:
        raise RuntimeError("Freshservice client not initialized. Check FRESHSERVICE_DOMAIN and FRESHSERVICE_APIKEY.")
    return _client


def _fmt(data: Any) -> str:
    """Pretty-print API response data."""
    if data is None:
        return "Operation completed successfully (no content returned)."
    return json.dumps(data, indent=2, default=str)


# ═══════════════════════════════════════════════════════════════════════════
# TICKETS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_tickets(page: int = 1, per_page: int = 30) -> str:
    """List all tickets with pagination.

    Args:
        page: Page number (starts at 1).
        per_page: Results per page (max 100).
    """
    c = _client_or_error()
    data = await c.get("tickets", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_ticket_by_id(ticket_id: int) -> str:
    """Retrieve a single ticket by ID, including conversations and stats.

    Args:
        ticket_id: The numeric ticket ID.
    """
    c = _client_or_error()
    data = await c.get(f"tickets/{ticket_id}", params={"include": "conversations,stats,requester"})
    return _fmt(data)


@mcp.tool()
async def create_ticket(
    subject: str,
    description: str,
    email: str,
    priority: int = 1,
    status: int = 2,
    source: int = 2,
    type: str = "Incident",
    group_id: int | None = None,
    responder_id: int | None = None,
    department_id: int | None = None,
    category: str | None = None,
    sub_category: str | None = None,
    tags: list[str] | None = None,
    cc_emails: list[str] | None = None,
    custom_fields: dict | None = None,
    workspace_id: int | None = None,
) -> str:
    """Create a new Freshservice ticket.

    Args:
        subject: Ticket subject line.
        description: Ticket description (HTML supported).
        email: Requester email. Creates a new contact if not found.
        priority: 1=Low, 2=Medium, 3=High, 4=Urgent.
        status: 2=Open, 3=Pending, 4=Resolved, 5=Closed.
        source: 1=Email, 2=Portal, 3=Phone, 4=Chat, 9=Walkup, 10=Slack.
        type: Ticket type (default "Incident").
        group_id: ID of assigned agent group.
        responder_id: ID of assigned agent.
        department_id: Department ID.
        category: Ticket category.
        sub_category: Ticket sub-category.
        tags: List of tags.
        cc_emails: CC email addresses.
        custom_fields: Custom field key-value pairs.
        workspace_id: Workspace ID (for multi-workspace accounts).
    """
    c = _client_or_error()
    body: dict[str, Any] = {
        "subject": subject,
        "description": description,
        "email": email,
        "priority": priority,
        "status": status,
        "source": source,
        "type": type,
    }
    if group_id is not None:
        body["group_id"] = group_id
    if responder_id is not None:
        body["responder_id"] = responder_id
    if department_id is not None:
        body["department_id"] = department_id
    if category is not None:
        body["category"] = category
    if sub_category is not None:
        body["sub_category"] = sub_category
    if tags:
        body["tags"] = tags
    if cc_emails:
        body["cc_emails"] = cc_emails
    if custom_fields:
        body["custom_fields"] = custom_fields
    if workspace_id is not None:
        body["workspace_id"] = workspace_id

    data = await c.post("tickets", body=body)
    return _fmt(data)


@mcp.tool()
async def update_ticket(ticket_id: int, updates: dict) -> str:
    """Update an existing ticket.

    Args:
        ticket_id: The ticket ID to update.
        updates: Dictionary of fields to update. Common fields: status, priority,
                 group_id, responder_id, subject, description, category, tags,
                 custom_fields, etc.
    """
    c = _client_or_error()
    data = await c.put(f"tickets/{ticket_id}", body=updates)
    return _fmt(data)


@mcp.tool()
async def delete_ticket(ticket_id: int) -> str:
    """Trash a ticket (soft delete).

    Args:
        ticket_id: The ticket ID to delete.
    """
    c = _client_or_error()
    await c.delete(f"tickets/{ticket_id}")
    return f"Ticket {ticket_id} has been deleted."


@mcp.tool()
async def filter_tickets(query: str, page: int = 1, per_page: int = 30) -> str:
    """Filter tickets using Freshservice query language.

    The query MUST be wrapped in double quotes. Examples:
      "status:2"  — open tickets
      "priority:4"  — urgent tickets
      "agent_id:1234 AND status:2"
      "group_id:5 AND priority:>2"
      "created_at:>'2024-01-01'"

    Args:
        query: Freshservice filter query string (must be in double quotes).
        page: Page number.
        per_page: Results per page (max 100).
    """
    c = _client_or_error()
    # Ensure query is wrapped in quotes for the API
    q = query.strip()
    if not q.startswith('"'):
        q = f'"{q}"'
    data = await c.get("tickets/filter", params={"query": q, "page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_ticket_fields() -> str:
    """Retrieve all ticket field definitions (built-in and custom)."""
    c = _client_or_error()
    data = await c.get("ticket_form_fields")
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# CONVERSATIONS (Ticket Replies & Notes)
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_ticket_conversations(ticket_id: int, page: int = 1, per_page: int = 30) -> str:
    """List all conversations (replies and notes) for a ticket.

    Args:
        ticket_id: The ticket ID.
        page: Page number.
        per_page: Results per page (max 100).
    """
    c = _client_or_error()
    data = await c.get(f"tickets/{ticket_id}/conversations", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def reply_to_ticket(ticket_id: int, body: str, cc_emails: list[str] | None = None) -> str:
    """Reply to a ticket (visible to requester).

    Args:
        ticket_id: The ticket ID.
        body: Reply body (HTML supported).
        cc_emails: Optional CC email addresses.
    """
    c = _client_or_error()
    payload: dict[str, Any] = {"body": body}
    if cc_emails:
        payload["cc_emails"] = cc_emails
    data = await c.post(f"tickets/{ticket_id}/reply", body=payload)
    return _fmt(data)


@mcp.tool()
async def add_ticket_note(ticket_id: int, body: str, private: bool = True) -> str:
    """Add a note to a ticket.

    Args:
        ticket_id: The ticket ID.
        body: Note body (HTML supported).
        private: True for private (agent-only) note, False for public.
    """
    c = _client_or_error()
    data = await c.post(f"tickets/{ticket_id}/notes", body={"body": body, "private": private})
    return _fmt(data)


@mcp.tool()
async def delete_ticket_note(ticket_id: int, conversation_id: int) -> str:
    """Delete a note from a ticket.

    Args:
        ticket_id: The ticket ID.
        conversation_id: The conversation (note) ID to delete.
    """
    c = _client_or_error()
    await c.delete(f"tickets/{ticket_id}/conversations/{conversation_id}")
    return "Note deleted successfully."


# ═══════════════════════════════════════════════════════════════════════════
# CHANGES
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_changes(page: int = 1, per_page: int = 30, query: str | None = None) -> str:
    """List all changes with optional filtering.

    Args:
        page: Page number.
        per_page: Results per page (max 100).
        query: Optional filter query, MUST be in double quotes. E.g. "status:3",
               "approval_status:1 AND status:<6".
    """
    c = _client_or_error()
    params: dict[str, Any] = {"page": page, "per_page": min(per_page, 100)}
    if query:
        q = query.strip()
        if not q.startswith('"'):
            q = f'"{q}"'
        params["query"] = q
    data = await c.get("changes", params=params)
    return _fmt(data)


@mcp.tool()
async def filter_changes(query: str, page: int = 1, per_page: int = 30) -> str:
    """Filter changes with advanced queries.

    Query MUST be wrapped in double quotes. Examples:
      "status:3"  — awaiting approval
      "approval_status:1"  — approved
      "approval_status:1 AND status:<6"  — approved but not closed

    Args:
        query: Freshservice filter query string.
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    q = query.strip()
    if not q.startswith('"'):
        q = f'"{q}"'
    data = await c.get("changes/filter", params={"query": q, "page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_change_by_id(change_id: int) -> str:
    """Retrieve a single change by ID.

    Args:
        change_id: The change ID.
    """
    c = _client_or_error()
    data = await c.get(f"changes/{change_id}")
    return _fmt(data)


@mcp.tool()
async def create_change(
    requester_id: int,
    subject: str,
    description: str,
    priority: int = 1,
    impact: int = 1,
    status: int = 1,
    risk: int = 1,
    change_type: int = 1,
    planned_start_date: str | None = None,
    planned_end_date: str | None = None,
    group_id: int | None = None,
    workspace_id: int | None = None,
    custom_fields: dict | None = None,
) -> str:
    """Create a new change request.

    Args:
        requester_id: ID of the requester.
        subject: Change subject.
        description: Change description (HTML supported).
        priority: 1=Low, 2=Medium, 3=High, 4=Urgent.
        impact: 1=Low, 2=Medium, 3=High.
        status: 1=Open, 2=Planning, 3=Awaiting Approval, 4=Pending Release,
                5=Pending Review, 6=Closed.
        risk: 1=Low, 2=Medium, 3=High, 4=Very High.
        change_type: 1=Minor, 2=Standard, 3=Major, 4=Emergency.
        planned_start_date: ISO 8601 datetime string.
        planned_end_date: ISO 8601 datetime string.
        group_id: Agent group ID.
        workspace_id: Workspace ID.
        custom_fields: Custom field key-value pairs.
    """
    c = _client_or_error()
    body: dict[str, Any] = {
        "requester_id": requester_id,
        "subject": subject,
        "description": description,
        "priority": priority,
        "impact": impact,
        "status": status,
        "risk": risk,
        "change_type": change_type,
    }
    if planned_start_date:
        body["planned_start_date"] = planned_start_date
    if planned_end_date:
        body["planned_end_date"] = planned_end_date
    if group_id is not None:
        body["group_id"] = group_id
    if workspace_id is not None:
        body["workspace_id"] = workspace_id
    if custom_fields:
        body["custom_fields"] = custom_fields

    data = await c.post("changes", body=body)
    return _fmt(data)


@mcp.tool()
async def update_change(change_id: int, change_fields: dict) -> str:
    """Update an existing change request.

    Args:
        change_id: The change ID.
        change_fields: Dictionary of fields to update. Common fields: status,
                       priority, impact, risk, subject, description, group_id, etc.
    """
    c = _client_or_error()
    data = await c.put(f"changes/{change_id}", body=change_fields)
    return _fmt(data)


@mcp.tool()
async def close_change(change_id: int, change_result_explanation: str) -> str:
    """Close a change with a result explanation.

    Args:
        change_id: The change ID.
        change_result_explanation: Explanation of the change result.
    """
    c = _client_or_error()
    data = await c.put(f"changes/{change_id}", body={
        "status": 6,
        "custom_fields": {"change_result_explanation": change_result_explanation},
    })
    return _fmt(data)


@mcp.tool()
async def delete_change(change_id: int) -> str:
    """Delete a change request.

    Args:
        change_id: The change ID.
    """
    c = _client_or_error()
    await c.delete(f"changes/{change_id}")
    return f"Change {change_id} has been deleted."


@mcp.tool()
async def get_change_tasks(change_id: int) -> str:
    """Get all tasks associated with a change.

    Args:
        change_id: The change ID.
    """
    c = _client_or_error()
    data = await c.get(f"changes/{change_id}/tasks")
    return _fmt(data)


@mcp.tool()
async def create_change_note(change_id: int, body: str, private: bool = True) -> str:
    """Add a note to a change request.

    Args:
        change_id: The change ID.
        body: Note body (HTML supported).
        private: True for agent-only note, False for public.
    """
    c = _client_or_error()
    data = await c.post(f"changes/{change_id}/notes", body={"body": body, "private": private})
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# ASSETS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_assets(page: int = 1, per_page: int = 30) -> str:
    """List all assets with pagination.

    Args:
        page: Page number.
        per_page: Results per page (max 100).
    """
    c = _client_or_error()
    data = await c.get("assets", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_asset_by_id(display_id: int) -> str:
    """Retrieve a single asset by its display ID.

    Args:
        display_id: The asset display ID.
    """
    c = _client_or_error()
    data = await c.get(f"assets/{display_id}")
    return _fmt(data)


@mcp.tool()
async def search_assets(query: str, page: int = 1, per_page: int = 30) -> str:
    """Search assets by various fields.

    Query examples:
      "name:'Dell Laptop'"
      "asset_tag:'ASSET-001'"
      "serial_number:'SN123'"
      "asset_state:'In Use'"

    Args:
        query: Asset search query.
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("assets", params={"search": query, "page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def filter_assets(query: str, page: int = 1, per_page: int = 30) -> str:
    """Filter assets using Freshservice query language.

    Args:
        query: Filter query. E.g. "asset_type_id:1", "department_id:5".
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    q = query.strip()
    if not q.startswith('"'):
        q = f'"{q}"'
    data = await c.get("assets/filter", params={"query": q, "page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def create_asset(
    name: str,
    asset_type_id: int,
    description: str | None = None,
    impact: int = 1,
    user_id: int | None = None,
    department_id: int | None = None,
    location_id: int | None = None,
    agent_id: int | None = None,
    asset_tag: str | None = None,
    custom_fields: dict | None = None,
) -> str:
    """Create a new asset.

    Args:
        name: Asset name.
        asset_type_id: Asset type ID (from get_asset_types).
        description: Asset description.
        impact: 1=Low, 2=Medium, 3=High.
        user_id: User assigned to the asset.
        department_id: Department ID.
        location_id: Location ID.
        agent_id: Agent managing the asset.
        asset_tag: Custom asset tag.
        custom_fields: Custom field key-value pairs.
    """
    c = _client_or_error()
    body: dict[str, Any] = {
        "name": name,
        "asset_type_id": asset_type_id,
        "impact": impact,
    }
    if description:
        body["description"] = description
    if user_id is not None:
        body["user_id"] = user_id
    if department_id is not None:
        body["department_id"] = department_id
    if location_id is not None:
        body["location_id"] = location_id
    if agent_id is not None:
        body["agent_id"] = agent_id
    if asset_tag:
        body["asset_tag"] = asset_tag
    if custom_fields:
        body["type_fields"] = custom_fields

    data = await c.post("assets", body=body)
    return _fmt(data)


@mcp.tool()
async def update_asset(display_id: int, updates: dict) -> str:
    """Update an existing asset.

    Args:
        display_id: The asset display ID.
        updates: Dictionary of fields to update.
    """
    c = _client_or_error()
    data = await c.put(f"assets/{display_id}", body=updates)
    return _fmt(data)


@mcp.tool()
async def delete_asset(display_id: int) -> str:
    """Delete an asset (soft delete / trash).

    Args:
        display_id: The asset display ID.
    """
    c = _client_or_error()
    await c.delete(f"assets/{display_id}")
    return f"Asset {display_id} has been deleted."


@mcp.tool()
async def get_asset_types(page: int = 1, per_page: int = 30) -> str:
    """List all asset types.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("asset_types", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# REQUESTERS / CONTACTS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_requesters(page: int = 1, per_page: int = 30) -> str:
    """List all requesters with pagination.

    Args:
        page: Page number.
        per_page: Results per page (max 100).
    """
    c = _client_or_error()
    data = await c.get("requesters", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_requester_by_id(requester_id: int) -> str:
    """Retrieve a single requester by ID.

    Args:
        requester_id: The requester ID.
    """
    c = _client_or_error()
    data = await c.get(f"requesters/{requester_id}")
    return _fmt(data)


@mcp.tool()
async def filter_requesters(query: str, page: int = 1, per_page: int = 30) -> str:
    """Filter requesters. Query examples: email, name, department, etc.

    Args:
        query: Filter query string.
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("requesters", params={"query": query, "page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def create_requester(
    first_name: str,
    email: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
    department_ids: list[int] | None = None,
    custom_fields: dict | None = None,
) -> str:
    """Create a new requester / contact.

    Args:
        first_name: Requester first name.
        email: Requester email address.
        last_name: Requester last name.
        phone: Phone number.
        department_ids: List of department IDs.
        custom_fields: Custom fields.
    """
    c = _client_or_error()
    body: dict[str, Any] = {"first_name": first_name}
    if email:
        body["primary_email"] = email
    if last_name:
        body["last_name"] = last_name
    if phone:
        body["phone"] = phone
    if department_ids:
        body["department_ids"] = department_ids
    if custom_fields:
        body["custom_fields"] = custom_fields

    data = await c.post("requesters", body=body)
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# AGENTS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_agents(page: int = 1, per_page: int = 30) -> str:
    """List all agents with pagination.

    Args:
        page: Page number.
        per_page: Results per page (max 100).
    """
    c = _client_or_error()
    data = await c.get("agents", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_agent_by_id(agent_id: int) -> str:
    """Retrieve a single agent by ID.

    Args:
        agent_id: The agent ID.
    """
    c = _client_or_error()
    data = await c.get(f"agents/{agent_id}")
    return _fmt(data)


@mcp.tool()
async def filter_agents(query: str, page: int = 1, per_page: int = 30) -> str:
    """Filter agents by various criteria.

    Args:
        query: Filter query (e.g. email, name, department, active status).
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("agents", params={"query": query, "page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# AGENT GROUPS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_agent_groups(page: int = 1, per_page: int = 30) -> str:
    """List all agent groups.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("groups", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_agent_group_by_id(group_id: int) -> str:
    """Get details of a specific agent group.

    Args:
        group_id: The group ID.
    """
    c = _client_or_error()
    data = await c.get(f"groups/{group_id}")
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# REQUESTER GROUPS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_requester_groups(page: int = 1, per_page: int = 30) -> str:
    """List all requester groups.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("requester_groups", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_requester_group_by_id(group_id: int) -> str:
    """Get details of a specific requester group.

    Args:
        group_id: The group ID.
    """
    c = _client_or_error()
    data = await c.get(f"requester_groups/{group_id}")
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_products(page: int = 1, per_page: int = 30) -> str:
    """List all products.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("products", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_product_by_id(product_id: int) -> str:
    """Get details of a specific product.

    Args:
        product_id: The product ID.
    """
    c = _client_or_error()
    data = await c.get(f"products/{product_id}")
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# WORKSPACES
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_workspaces(page: int = 1, per_page: int = 30) -> str:
    """List all workspaces.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("workspaces", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# CANNED RESPONSES
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_canned_response_folders() -> str:
    """List all canned response folders."""
    c = _client_or_error()
    data = await c.get("canned_response_folders")
    return _fmt(data)


@mcp.tool()
async def get_canned_responses_in_folder(folder_id: int) -> str:
    """List all canned responses within a folder.

    Args:
        folder_id: The canned response folder ID.
    """
    c = _client_or_error()
    data = await c.get(f"canned_response_folders/{folder_id}/canned_responses")
    return _fmt(data)


@mcp.tool()
async def get_canned_response(response_id: int) -> str:
    """Get a specific canned response by ID.

    Args:
        response_id: The canned response ID.
    """
    c = _client_or_error()
    data = await c.get(f"canned_responses/{response_id}")
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# SOLUTION CATEGORIES / FOLDERS / ARTICLES (Knowledge Base)
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_solution_categories(page: int = 1, per_page: int = 30) -> str:
    """List all solution (knowledge base) categories.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("solutions/categories", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_solution_category_by_id(category_id: int) -> str:
    """View a specific solution category.

    Args:
        category_id: The category ID.
    """
    c = _client_or_error()
    data = await c.get(f"solutions/categories/{category_id}")
    return _fmt(data)


@mcp.tool()
async def create_solution_category(name: str, description: str | None = None) -> str:
    """Create a new solution category.

    Args:
        name: Category name.
        description: Category description.
    """
    c = _client_or_error()
    body: dict[str, Any] = {"name": name}
    if description:
        body["description"] = description
    data = await c.post("solutions/categories", body=body)
    return _fmt(data)


@mcp.tool()
async def get_solution_folders(category_id: int, page: int = 1, per_page: int = 30) -> str:
    """List all solution folders in a category.

    Args:
        category_id: The parent category ID.
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get(
        f"solutions/categories/{category_id}/folders",
        params={"page": page, "per_page": min(per_page, 100)},
    )
    return _fmt(data)


@mcp.tool()
async def get_solution_folder_by_id(folder_id: int) -> str:
    """View a specific solution folder.

    Args:
        folder_id: The folder ID.
    """
    c = _client_or_error()
    data = await c.get(f"solutions/folders/{folder_id}")
    return _fmt(data)


@mcp.tool()
async def create_solution_folder(
    category_id: int,
    name: str,
    description: str | None = None,
    visibility: int = 1,
) -> str:
    """Create a new solution folder.

    Args:
        category_id: Parent category ID.
        name: Folder name.
        description: Folder description.
        visibility: 1=All, 2=Logged-in users, 3=Agents only.
    """
    c = _client_or_error()
    body: dict[str, Any] = {"name": name, "visibility": visibility}
    if description:
        body["description"] = description
    data = await c.post(f"solutions/categories/{category_id}/folders", body=body)
    return _fmt(data)


@mcp.tool()
async def get_solution_articles(folder_id: int, page: int = 1, per_page: int = 30) -> str:
    """List all solution articles in a folder.

    Args:
        folder_id: The parent folder ID.
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get(
        f"solutions/folders/{folder_id}/articles",
        params={"page": page, "per_page": min(per_page, 100)},
    )
    return _fmt(data)


@mcp.tool()
async def get_solution_article_by_id(article_id: int) -> str:
    """View a specific solution article.

    Args:
        article_id: The article ID.
    """
    c = _client_or_error()
    data = await c.get(f"solutions/articles/{article_id}")
    return _fmt(data)


@mcp.tool()
async def create_solution_article(
    folder_id: int,
    title: str,
    description: str,
    status: int = 1,
    article_type: int = 1,
    tags: list[str] | None = None,
) -> str:
    """Create a new solution article.

    Args:
        folder_id: Parent folder ID.
        title: Article title.
        description: Article body (HTML supported).
        status: 1=Draft, 2=Published.
        article_type: 1=Permanent, 2=Workaround.
        tags: Optional list of tags.
    """
    c = _client_or_error()
    body: dict[str, Any] = {
        "title": title,
        "description": description,
        "status": status,
        "article_type": article_type,
    }
    if tags:
        body["tags"] = tags
    data = await c.post(f"solutions/folders/{folder_id}/articles", body=body)
    return _fmt(data)


@mcp.tool()
async def search_solution_articles(search_term: str) -> str:
    """Search solution articles by keyword.

    Args:
        search_term: Text to search for in articles.
    """
    c = _client_or_error()
    data = await c.get("solutions/articles", params={"search_term": search_term})
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# PROBLEMS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_problems(page: int = 1, per_page: int = 30) -> str:
    """List all problems with pagination.

    Args:
        page: Page number.
        per_page: Results per page (max 100).
    """
    c = _client_or_error()
    data = await c.get("problems", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_problem_by_id(problem_id: int) -> str:
    """Retrieve a single problem by ID.

    Args:
        problem_id: The problem ID.
    """
    c = _client_or_error()
    data = await c.get(f"problems/{problem_id}")
    return _fmt(data)


@mcp.tool()
async def create_problem(
    subject: str,
    description: str,
    requester_id: int,
    priority: int = 1,
    impact: int = 1,
    status: int = 1,
    group_id: int | None = None,
    custom_fields: dict | None = None,
) -> str:
    """Create a new problem.

    Args:
        subject: Problem subject.
        description: Problem description (HTML).
        requester_id: Requester ID.
        priority: 1=Low, 2=Medium, 3=High, 4=Urgent.
        impact: 1=Low, 2=Medium, 3=High.
        status: 1=Open, 2=Change Requested, 3=Closed.
        group_id: Agent group ID.
        custom_fields: Custom fields.
    """
    c = _client_or_error()
    body: dict[str, Any] = {
        "subject": subject,
        "description": description,
        "requester_id": requester_id,
        "priority": priority,
        "impact": impact,
        "status": status,
    }
    if group_id is not None:
        body["group_id"] = group_id
    if custom_fields:
        body["custom_fields"] = custom_fields
    data = await c.post("problems", body=body)
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# DEPARTMENTS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_departments(page: int = 1, per_page: int = 30) -> str:
    """List all departments.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("departments", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_department_by_id(department_id: int) -> str:
    """View a specific department.

    Args:
        department_id: The department ID.
    """
    c = _client_or_error()
    data = await c.get(f"departments/{department_id}")
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# LOCATIONS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_locations(page: int = 1, per_page: int = 30) -> str:
    """List all locations.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("locations", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# SOFTWARE
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_software(page: int = 1, per_page: int = 30) -> str:
    """List all software entries.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("applications", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_software_by_id(software_id: int) -> str:
    """View a specific software entry.

    Args:
        software_id: The software ID.
    """
    c = _client_or_error()
    data = await c.get(f"applications/{software_id}")
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# VENDORS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_vendors(page: int = 1, per_page: int = 30) -> str:
    """List all vendors.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("vendors", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# SERVICE CATALOG
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_service_catalog_items(page: int = 1, per_page: int = 30) -> str:
    """List all service catalog items.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("service_catalog/items", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_service_catalog_item(item_id: int) -> str:
    """View a specific service catalog item.

    Args:
        item_id: The service catalog item ID.
    """
    c = _client_or_error()
    data = await c.get(f"service_catalog/items/{item_id}")
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# ANNOUNCEMENTS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_announcements(page: int = 1, per_page: int = 30) -> str:
    """List all announcements.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("announcements", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# CONTRACTS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_contracts(page: int = 1, per_page: int = 30) -> str:
    """List all contracts.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("contracts", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


@mcp.tool()
async def get_contract_by_id(contract_id: int) -> str:
    """View a specific contract.

    Args:
        contract_id: The contract ID.
    """
    c = _client_or_error()
    data = await c.get(f"contracts/{contract_id}")
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# PURCHASE ORDERS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_purchase_orders(page: int = 1, per_page: int = 30) -> str:
    """List all purchase orders.

    Args:
        page: Page number.
        per_page: Results per page.
    """
    c = _client_or_error()
    data = await c.get("purchase_orders", params={"page": page, "per_page": min(per_page, 100)})
    return _fmt(data)


# ═══════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════


def main():
    """Run the Freshservice MCP server via stdio transport."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
