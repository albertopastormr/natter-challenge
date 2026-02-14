"""Tests for the Crawler with a mock HTTP client.

Verifies the full crawl flow (discovery → pagination → extraction)
without making any network calls.
"""

from __future__ import annotations
import pytest

pytestmark = [pytest.mark.unit, pytest.mark.anyio]

from tests.conftest import (
    BASE_URL,
    HOMEPAGE_HTML,
    LISTING_PAGE_HTML,
    P31_ID,
    P31_NAME,
    P32_ID,
    P32_NAME,
    P32_VARIANTS,
    PRODUCT_DETAIL_NO_VARIANTS,
    PRODUCT_DETAIL_WITH_VARIANTS,
)
from src.scrapers.crawler import Crawler
from src.scrapers.parser import WebScraperIoProvider


# ---------------------------------------------------------------------------
# Mock HTTP client
# ---------------------------------------------------------------------------


class MockHttpClient:
    """Returns pre-defined HTML for specific URL patterns."""

    def __init__(self, responses: dict[str, str]) -> None:
        self._responses = responses
        self.fetched_urls: list[str] = []

    async def fetch(self, url: str) -> str:
        self.fetched_urls.append(url)
        
        # 1. Try exact match first (highest priority)
        if url in self._responses:
            return self._responses[url]
        
        # 2. Try specific patterns (longest path segments first)
        # Exclude the BASE_URL from this search to avoid it eating all sub-URLs
        specific_responses = {k: v for k, v in self._responses.items() if k != BASE_URL}
        sorted_patterns = sorted(specific_responses.keys(), key=len, reverse=True)
        
        for pattern in sorted_patterns:
            if pattern in url:
                return specific_responses[pattern]
        
        # 3. Fallback to BASE_URL if it was in url and nothing else matched
        if BASE_URL in url and BASE_URL in self._responses:
            return self._responses[BASE_URL]
            
        return "<html><body></body></html>"

    async def __aenter__(self) -> MockHttpClient:
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCrawler:
    def _make_client(self) -> MockHttpClient:
        responses = {
            BASE_URL: HOMEPAGE_HTML,
            "/computers/laptops": LISTING_PAGE_HTML,
            f"/product/{P31_ID}": PRODUCT_DETAIL_NO_VARIANTS,
            f"/product/{P32_ID}": PRODUCT_DETAIL_WITH_VARIANTS,
        }
        return MockHttpClient(responses)

    async def test_fetches_homepage_first(self) -> None:
        client = self._make_client()
        provider = WebScraperIoProvider()
        crawler = Crawler(client=client, provider=provider)
        await crawler.crawl()

        # The first URL fetched should be the base_url
        assert client.fetched_urls[0] == BASE_URL

    async def test_crawl_returns_products(self) -> None:
        client = self._make_client()
        provider = WebScraperIoProvider()
        crawler = Crawler(client=client, provider=provider)
        products = await crawler.crawl()

        # 1 from P31 + 3 variants from P32 = 4 total
        assert len(products) == 4

    async def test_crawl_product_names(self) -> None:
        client = self._make_client()
        provider = WebScraperIoProvider()
        crawler = Crawler(client=client, provider=provider)
        products = await crawler.crawl()
        names = [p.name for p in products]
        
        assert P31_NAME in names
        # P32 should have HDD: label now due to provider refactor
        for swatch in P32_VARIANTS:
            assert f"{P32_NAME} HDD: {swatch}" in names

    async def test_deduplicates_product_urls(self) -> None:
        """Even if the same product URL appears on multiple pages,
        we should only visit it once."""
        client = self._make_client()
        provider = WebScraperIoProvider()
        crawler = Crawler(client=client, provider=provider)
        await crawler.crawl()

        p31_visits = [url for url in client.fetched_urls if f"/product/{P31_ID}" in url]
        assert len(p31_visits) == 1

    async def test_handles_empty_subcategories(self) -> None:
        client = MockHttpClient({BASE_URL: HOMEPAGE_HTML})
        provider = WebScraperIoProvider()
        crawler = Crawler(client=client, provider=provider)
        products = await crawler.crawl()
        assert len(products) == 0

    async def test_handles_failed_product_page(self) -> None:
        # Mock client returns default empty HTML if URL not found
        client = MockHttpClient(
            {
                BASE_URL: HOMEPAGE_HTML,
                "/computers/laptops": LISTING_PAGE_HTML,
                # Product 32 is present, but 31 is missing
                f"/product/{P32_ID}": PRODUCT_DETAIL_WITH_VARIANTS,
            }
        )
        provider = WebScraperIoProvider()
        crawler = Crawler(client=client, provider=provider)
        products = await crawler.crawl()
        
        # Should still have products from P32
        assert len(products) == 3
        # Should have logged an error but didn't crash
