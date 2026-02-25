"""Freshservice API client with proper auth, pagination, and error handling."""

from __future__ import annotations

import base64
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class FreshserviceAPIError(Exception):
    """Raised when the Freshservice API returns an error."""

    def __init__(self, status_code: int, message: str, errors: list[dict] | None = None):
        self.status_code = status_code
        self.message = message
        self.errors = errors or []
        super().__init__(f"HTTP {status_code}: {message}")


class FreshserviceClient:
    """Async HTTP client for the Freshservice v2 REST API."""

    def __init__(self, domain: str | None = None, api_key: str | None = None):
        self.domain = domain or os.environ.get("FRESHSERVICE_DOMAIN", "")
        self.api_key = api_key or os.environ.get("FRESHSERVICE_APIKEY", "")

        if not self.domain:
            raise ValueError(
                "FRESHSERVICE_DOMAIN is required. Set it as an environment variable "
                "or pass it directly. Example: yourcompany.freshservice.com"
            )
        if not self.api_key:
            raise ValueError(
                "FRESHSERVICE_APIKEY is required. Set it as an environment variable "
                "or pass it directly. Find it under Profile Settings → API Settings."
            )

        # Normalize domain - strip protocol and trailing slashes
        self.domain = self.domain.strip().rstrip("/")
        if self.domain.startswith("http://"):
            self.domain = self.domain[7:]
        if self.domain.startswith("https://"):
            self.domain = self.domain[8:]

        self.base_url = f"https://{self.domain}/api/v2"

        # Build Basic Auth header: base64(api_key:X)
        credentials = base64.b64encode(f"{self.api_key}:X".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        self._client = httpx.AsyncClient(
            headers=self._headers,
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
        )

    async def close(self):
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list | None:
        """Make an API request and handle errors."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Filter out None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        logger.debug(f"{method} {url} params={params} body={json_body}")

        response = await self._client.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
        )

        # Log rate limit info
        remaining = response.headers.get("X-Ratelimit-Remaining")
        if remaining:
            logger.debug(f"Rate limit remaining: {remaining}")

        if response.status_code == 204:
            return None  # Successful delete, no content

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            raise FreshserviceAPIError(
                429,
                f"Rate limit exceeded. Retry after {retry_after} seconds.",
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                msg = error_data.get("description", error_data.get("message", response.text))
                errors = error_data.get("errors", [])
            except Exception:
                msg = response.text
                errors = []
            raise FreshserviceAPIError(response.status_code, msg, errors)

        if not response.text.strip():
            return None

        return response.json()

    # Convenience methods
    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, body: dict[str, Any] | None = None) -> Any:
        return await self._request("POST", endpoint, json_body=body)

    async def put(self, endpoint: str, body: dict[str, Any] | None = None) -> Any:
        return await self._request("PUT", endpoint, json_body=body)

    async def delete(self, endpoint: str) -> Any:
        return await self._request("DELETE", endpoint)
