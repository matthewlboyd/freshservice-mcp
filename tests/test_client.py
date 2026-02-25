"""Unit tests for FreshserviceClient."""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from freshservice_mcp.client import FreshserviceClient, FreshserviceAPIError


def make_response(status_code: int, json_data=None, text: str = ""):
    """Build a mock httpx Response."""
    response = MagicMock()
    response.status_code = status_code
    response.text = text if json_data is None else ""
    response.headers = {}
    if json_data is not None:
        response.text = ""
        response.json = MagicMock(return_value=json_data)
        response.text = str(json_data)  # non-empty so it parses
    else:
        response.json = MagicMock(side_effect=Exception("no body"))
    return response


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestClientInit:
    def test_raises_if_domain_missing(self, monkeypatch):
        monkeypatch.delenv("FRESHSERVICE_DOMAIN", raising=False)
        monkeypatch.delenv("FRESHSERVICE_APIKEY", raising=False)
        with pytest.raises(ValueError, match="FRESHSERVICE_DOMAIN"):
            FreshserviceClient(domain="", api_key="somekey")

    def test_raises_if_apikey_missing(self, monkeypatch):
        monkeypatch.delenv("FRESHSERVICE_APIKEY", raising=False)
        with pytest.raises(ValueError, match="FRESHSERVICE_APIKEY"):
            FreshserviceClient(domain="example.freshservice.com", api_key="")

    def test_strips_https_prefix(self):
        c = FreshserviceClient(domain="https://example.freshservice.com", api_key="key")
        assert c.domain == "example.freshservice.com"
        assert c.base_url == "https://example.freshservice.com/api/v2"

    def test_strips_http_prefix(self):
        c = FreshserviceClient(domain="http://example.freshservice.com", api_key="key")
        assert c.domain == "example.freshservice.com"

    def test_strips_trailing_slash(self):
        c = FreshserviceClient(domain="example.freshservice.com/", api_key="key")
        assert c.domain == "example.freshservice.com"

    def test_strips_whitespace(self):
        c = FreshserviceClient(domain="  example.freshservice.com  ", api_key="key")
        assert c.domain == "example.freshservice.com"

    def test_auth_header_is_basic_base64(self):
        c = FreshserviceClient(domain="example.freshservice.com", api_key="mykey")
        expected = base64.b64encode(b"mykey:X").decode()
        assert c._headers["Authorization"] == f"Basic {expected}"

    def test_content_type_header(self):
        c = FreshserviceClient(domain="example.freshservice.com", api_key="mykey")
        assert c._headers["Content-Type"] == "application/json"
        assert c._headers["Accept"] == "application/json"

    def test_reads_domain_from_env(self, monkeypatch):
        monkeypatch.setenv("FRESHSERVICE_DOMAIN", "env.freshservice.com")
        monkeypatch.setenv("FRESHSERVICE_APIKEY", "envkey")
        c = FreshserviceClient()
        assert c.domain == "env.freshservice.com"


# ---------------------------------------------------------------------------
# _request error handling
# ---------------------------------------------------------------------------

class TestClientRequest:
    def _make_client(self):
        return FreshserviceClient(domain="example.freshservice.com", api_key="key")

    async def _mock_request(self, client, status_code, json_data=None, text="", headers=None):
        """Patch the internal httpx client and call _request."""
        response = MagicMock()
        response.status_code = status_code
        response.headers = headers or {}
        if json_data is not None:
            response.text = "non-empty"
            response.json = MagicMock(return_value=json_data)
        else:
            response.text = text
            response.json = MagicMock(side_effect=Exception("no body"))
        client._client.request = AsyncMock(return_value=response)
        return await client._request("GET", "tickets")

    @pytest.mark.asyncio
    async def test_204_returns_none(self):
        c = self._make_client()
        result = await self._mock_request(c, 204)
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_body_returns_none(self):
        c = self._make_client()
        result = await self._mock_request(c, 200, text="   ")
        assert result is None

    @pytest.mark.asyncio
    async def test_200_returns_json(self):
        c = self._make_client()
        result = await self._mock_request(c, 200, json_data={"tickets": []})
        assert result == {"tickets": []}

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self):
        c = self._make_client()
        with pytest.raises(FreshserviceAPIError) as exc_info:
            await self._mock_request(c, 429, headers={"Retry-After": "30"})
        assert exc_info.value.status_code == 429
        assert "Rate limit" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_401_raises_api_error(self):
        c = self._make_client()
        with pytest.raises(FreshserviceAPIError) as exc_info:
            await self._mock_request(
                c, 401,
                json_data={"description": "Unauthorized", "errors": []},
            )
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_404_raises_api_error(self):
        c = self._make_client()
        with pytest.raises(FreshserviceAPIError) as exc_info:
            await self._mock_request(
                c, 404,
                json_data={"description": "Record not found", "errors": []},
            )
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_500_raises_api_error_with_text_fallback(self):
        c = self._make_client()
        response = MagicMock()
        response.status_code = 500
        response.headers = {}
        response.text = "Internal Server Error"
        response.json = MagicMock(side_effect=Exception("not json"))
        c._client.request = AsyncMock(return_value=response)
        with pytest.raises(FreshserviceAPIError) as exc_info:
            await c._request("GET", "tickets")
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_none_params_are_filtered(self):
        c = self._make_client()
        response = MagicMock()
        response.status_code = 200
        response.headers = {}
        response.text = "non-empty"
        response.json = MagicMock(return_value={})
        c._client.request = AsyncMock(return_value=response)
        await c._request("GET", "tickets", params={"page": 1, "group_id": None})
        call_kwargs = c._client.request.call_args
        assert call_kwargs.kwargs["params"] == {"page": 1}
