"""Tests for remaining modules: problems, products, workspaces, canned responses,
departments, locations, software, vendors, service catalog, announcements,
contracts, purchase orders."""

import pytest
from freshservice_mcp.server import (
    # Problems
    get_problems,
    get_problem_by_id,
    create_problem,
    # Products
    get_products,
    get_product_by_id,
    # Workspaces
    get_workspaces,
    # Canned Responses
    get_canned_response_folders,
    get_canned_responses_in_folder,
    get_canned_response,
    # Departments
    get_departments,
    get_department_by_id,
    # Locations
    get_locations,
    # Software
    get_software,
    get_software_by_id,
    # Vendors
    get_vendors,
    # Service Catalog
    get_service_catalog_items,
    get_service_catalog_item,
    # Announcements
    get_announcements,
    # Contracts
    get_contracts,
    get_contract_by_id,
    # Purchase Orders
    get_purchase_orders,
)


# ---------------------------------------------------------------------------
# Problems
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_problems(mock_client):
    await get_problems()
    mock_client.get.assert_called_once_with(
        "problems", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_problems_caps_per_page(mock_client):
    await get_problems(per_page=200)
    assert mock_client.get.call_args.kwargs["params"]["per_page"] == 100


@pytest.mark.asyncio
async def test_get_problem_by_id(mock_client):
    await get_problem_by_id(15)
    mock_client.get.assert_called_once_with("problems/15")


@pytest.mark.asyncio
async def test_create_problem_minimal(mock_client):
    await create_problem(
        subject="Database instability",
        description="DB goes down randomly",
        requester_id=3,
    )
    body = mock_client.post.call_args.kwargs["body"]
    assert body["subject"] == "Database instability"
    assert body["requester_id"] == 3
    assert body["priority"] == 1
    assert body["impact"] == 1
    assert body["status"] == 1
    assert "group_id" not in body


@pytest.mark.asyncio
async def test_create_problem_with_group_and_custom_fields(mock_client):
    await create_problem(
        subject="Network outage",
        description="All offices affected",
        requester_id=3,
        priority=4,
        impact=3,
        group_id=7,
        custom_fields={"cf_root_cause": "router failure"},
    )
    body = mock_client.post.call_args.kwargs["body"]
    assert body["priority"] == 4
    assert body["impact"] == 3
    assert body["group_id"] == 7
    assert body["custom_fields"] == {"cf_root_cause": "router failure"}


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_products(mock_client):
    await get_products()
    mock_client.get.assert_called_once_with(
        "products", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_product_by_id(mock_client):
    await get_product_by_id(20)
    mock_client.get.assert_called_once_with("products/20")


# ---------------------------------------------------------------------------
# Workspaces
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_workspaces(mock_client):
    await get_workspaces()
    mock_client.get.assert_called_once_with(
        "workspaces", params={"page": 1, "per_page": 30}
    )


# ---------------------------------------------------------------------------
# Canned Responses
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_canned_response_folders(mock_client):
    await get_canned_response_folders()
    mock_client.get.assert_called_once_with("canned_response_folders")


@pytest.mark.asyncio
async def test_get_canned_responses_in_folder(mock_client):
    await get_canned_responses_in_folder(4)
    mock_client.get.assert_called_once_with(
        "canned_response_folders/4/canned_responses"
    )


@pytest.mark.asyncio
async def test_get_canned_response(mock_client):
    await get_canned_response(17)
    mock_client.get.assert_called_once_with("canned_responses/17")


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_departments(mock_client):
    await get_departments()
    mock_client.get.assert_called_once_with(
        "departments", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_department_by_id(mock_client):
    await get_department_by_id(6)
    mock_client.get.assert_called_once_with("departments/6")


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_locations(mock_client):
    await get_locations()
    mock_client.get.assert_called_once_with(
        "locations", params={"page": 1, "per_page": 30}
    )


# ---------------------------------------------------------------------------
# Software
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_software(mock_client):
    await get_software()
    mock_client.get.assert_called_once_with(
        "applications", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_software_by_id(mock_client):
    await get_software_by_id(88)
    mock_client.get.assert_called_once_with("applications/88")


# ---------------------------------------------------------------------------
# Vendors
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_vendors(mock_client):
    await get_vendors()
    mock_client.get.assert_called_once_with(
        "vendors", params={"page": 1, "per_page": 30}
    )


# ---------------------------------------------------------------------------
# Service Catalog
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_service_catalog_items(mock_client):
    await get_service_catalog_items()
    mock_client.get.assert_called_once_with(
        "service_catalog/items", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_service_catalog_item(mock_client):
    await get_service_catalog_item(11)
    mock_client.get.assert_called_once_with("service_catalog/items/11")


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_announcements(mock_client):
    await get_announcements()
    mock_client.get.assert_called_once_with(
        "announcements", params={"page": 1, "per_page": 30}
    )


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_contracts(mock_client):
    await get_contracts()
    mock_client.get.assert_called_once_with(
        "contracts", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_contract_by_id(mock_client):
    await get_contract_by_id(25)
    mock_client.get.assert_called_once_with("contracts/25")


# ---------------------------------------------------------------------------
# Purchase Orders
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_purchase_orders(mock_client):
    await get_purchase_orders()
    mock_client.get.assert_called_once_with(
        "purchase_orders", params={"page": 1, "per_page": 30}
    )
