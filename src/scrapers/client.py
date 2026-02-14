"""HTTP client wrapper with timeout handling and graceful error reporting."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

import httpx

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; NatterScraper/1.0; +https://github.com/natter)"


# ---------------------------------------------------------------------------
# Protocol (for dependency injection / testing)
# ---------------------------------------------------------------------------


class HttpClientProtocol(Protocol):
    """Interface for async HTTP client implementations."""

    async def fetch(self, url: str) -> str:
        """Fetch content from a URL."""
        ...


# ---------------------------------------------------------------------------
# Concrete implementation
# ---------------------------------------------------------------------------


class HttpClient:
    """Production async HTTP client using httpx."""

    def __init__(self, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def fetch(self, url: str) -> str:
        """Fetch *url* and return the response body.

        Raises ``httpx.HTTPStatusError`` for 4xx/5xx and
        ``httpx.TimeoutException`` for network timeouts.
        """
        logger.debug("GET %s", url)
        response = await self._client.get(url)
        response.raise_for_status()
        return response.text

    # ------------------------------------------------------------------
    # Context-manager support
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> HttpClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()


# --- Static type check (for mypy only) ---
if TYPE_CHECKING:
    # This ensures HttpClient satisfies HttpClientProtocol
    # (Since it requires an event loop, we just cast for type checking)
    from typing import cast
    _ = cast(HttpClientProtocol, HttpClient())
