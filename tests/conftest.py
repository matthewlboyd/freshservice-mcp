"""Shared fixtures for all tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock

import freshservice_mcp.server as server_module


@pytest.fixture
def mock_client(monkeypatch):
    """Inject a mock FreshserviceClient into the server module."""
    client = MagicMock()
    client.get = AsyncMock(return_value={"items": []})
    client.post = AsyncMock(return_value={"item": {}})
    client.put = AsyncMock(return_value={"item": {}})
    client.delete = AsyncMock(return_value=None)
    monkeypatch.setattr(server_module, "_client", client)
    return client
