"""Tests for knowledge base (solution categories, folders, articles) tools."""

import pytest
from freshservice_mcp.server import (
    get_solution_categories,
    get_solution_category_by_id,
    create_solution_category,
    get_solution_folders,
    get_solution_folder_by_id,
    create_solution_folder,
    get_solution_articles,
    get_solution_article_by_id,
    create_solution_article,
    search_solution_articles,
)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_solution_categories(mock_client):
    await get_solution_categories()
    mock_client.get.assert_called_once_with(
        "solutions/categories", params={"page": 1, "per_page": 30}
    )


@pytest.mark.asyncio
async def test_get_solution_categories_caps_per_page(mock_client):
    await get_solution_categories(per_page=500)
    params = mock_client.get.call_args.kwargs["params"]
    assert params["per_page"] == 100


@pytest.mark.asyncio
async def test_get_solution_category_by_id(mock_client):
    await get_solution_category_by_id(5)
    mock_client.get.assert_called_once_with("solutions/categories/5")


@pytest.mark.asyncio
async def test_create_solution_category_minimal(mock_client):
    await create_solution_category(name="IT Guides")
    body = mock_client.post.call_args.kwargs["body"]
    assert body["name"] == "IT Guides"
    assert "description" not in body


@pytest.mark.asyncio
async def test_create_solution_category_with_description(mock_client):
    await create_solution_category(name="IT Guides", description="All IT guides")
    body = mock_client.post.call_args.kwargs["body"]
    assert body["description"] == "All IT guides"


# ---------------------------------------------------------------------------
# Folders
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_solution_folders(mock_client):
    await get_solution_folders(category_id=5)
    mock_client.get.assert_called_once_with(
        "solutions/categories/5/folders",
        params={"page": 1, "per_page": 30},
    )


@pytest.mark.asyncio
async def test_get_solution_folder_by_id(mock_client):
    await get_solution_folder_by_id(12)
    mock_client.get.assert_called_once_with("solutions/folders/12")


@pytest.mark.asyncio
async def test_create_solution_folder_minimal(mock_client):
    await create_solution_folder(category_id=5, name="Onboarding")
    mock_client.post.assert_called_once_with(
        "solutions/categories/5/folders",
        body={"name": "Onboarding", "visibility": 1},
    )


@pytest.mark.asyncio
async def test_create_solution_folder_with_description_and_visibility(mock_client):
    await create_solution_folder(
        category_id=5,
        name="Internal",
        description="Agents only",
        visibility=3,
    )
    body = mock_client.post.call_args.kwargs["body"]
    assert body["description"] == "Agents only"
    assert body["visibility"] == 3


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_solution_articles(mock_client):
    await get_solution_articles(folder_id=12)
    mock_client.get.assert_called_once_with(
        "solutions/folders/12/articles",
        params={"page": 1, "per_page": 30},
    )


@pytest.mark.asyncio
async def test_get_solution_article_by_id(mock_client):
    await get_solution_article_by_id(99)
    mock_client.get.assert_called_once_with("solutions/articles/99")


@pytest.mark.asyncio
async def test_create_solution_article_minimal(mock_client):
    await create_solution_article(
        folder_id=12,
        title="How to reset password",
        description="Step by step instructions...",
    )
    body = mock_client.post.call_args.kwargs["body"]
    assert body["title"] == "How to reset password"
    assert body["description"] == "Step by step instructions..."
    assert body["status"] == 1
    assert body["article_type"] == 1
    assert "tags" not in body


@pytest.mark.asyncio
async def test_create_solution_article_with_tags(mock_client):
    await create_solution_article(
        folder_id=12,
        title="VPN Setup",
        description="Connect to VPN...",
        status=2,
        article_type=1,
        tags=["vpn", "remote"],
    )
    body = mock_client.post.call_args.kwargs["body"]
    assert body["status"] == 2
    assert body["tags"] == ["vpn", "remote"]


@pytest.mark.asyncio
async def test_create_solution_article_endpoint(mock_client):
    await create_solution_article(folder_id=12, title="T", description="D")
    mock_client.post.assert_called_once()
    endpoint = mock_client.post.call_args.args[0]
    assert endpoint == "solutions/folders/12/articles"


@pytest.mark.asyncio
async def test_search_solution_articles(mock_client):
    await search_solution_articles("password reset")
    mock_client.get.assert_called_once_with(
        "solutions/articles", params={"search_term": "password reset"}
    )
