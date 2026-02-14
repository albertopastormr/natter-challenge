"""Async Crawler implementation."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.models import Product
    from src.scrapers.client import HttpClientProtocol
    from src.scrapers.base import BaseScraperProvider

logger = logging.getLogger(__name__)


class Crawler:
    """Orchestrates async discovery and extraction of products."""

    def __init__(
        self,
        client: HttpClientProtocol,
        provider: BaseScraperProvider,
    ) -> None:
        self._client = client
        self._provider = provider
        self._base_url = provider.base_url.rstrip("/")

    async def crawl(self) -> list[Product]:
        """Run the full async crawl and return a flat list of products."""
        logger.info("Starting async crawl from %s", self._base_url)

        # 1. Discovery
        subcategories = await self._discover_subcategories()
        logger.info("Discovered %d subcategories", len(subcategories))

        # 2. Listing URLs
        product_urls = await self._collect_product_urls(subcategories)
        logger.info("Found %d product links", len(product_urls))

        # 3. Extraction
        products = await self._extract_products(product_urls)
        logger.info("Extraction complete. Total products: %d", len(products))

        return products

    async def _discover_subcategories(self) -> list[str]:
        """Recursively discover all category URLs starting from base_url."""
        visited = {self._base_url}
        to_visit = [self._base_url]
        results: set[str] = set()

        while to_visit:
            current = to_visit.pop(0)
            try:
                html = await self._client.fetch(current)
                found = self._provider.parse_subcategory_urls(html, current)

                for url in found:
                    if url not in visited:
                        visited.add(url)
                        to_visit.append(url)
                        results.add(url)
            except Exception as exc:
                logger.error("Failed to discover from %s: %s", current, exc)

        return sorted(list(results))

    async def _collect_product_urls(self, subcategories: list[str]) -> list[str]:
        """Iterate through every page of every subcategory."""
        seen: set[str] = set()
        ordered: list[str] = []

        # We could use asyncio.gather here for speed, but let's keep it sequential
        # per subcategory to avoid overwhelming the server, or gather with a limit.
        for sub_url in subcategories:
            try:
                html = await self._client.fetch(sub_url)
                await self._collect_from_page(sub_url, seen, ordered, html=html)

                page_urls = self._provider.parse_pagination_urls(html, sub_url)
                for page_url in page_urls:
                    await self._collect_from_page(page_url, seen, ordered)
            except Exception as exc:
                logger.error("Failed to collect from %s: %s", sub_url, exc)

        return ordered

    async def _collect_from_page(
        self,
        page_url: str,
        seen: set[str],
        ordered: list[str],
        html: str | None = None,
    ) -> None:
        """Fetch one listing page (if html not provided) and add its product URLs."""
        try:
            content = html if html is not None else await self._client.fetch(page_url)
            for url in self._provider.parse_product_urls(content, page_url):
                if url not in seen:
                    seen.add(url)
                    ordered.append(url)
        except Exception as exc:
            logger.error("Failed to fetch page %s: %s", page_url, exc)

    async def _extract_products(self, product_urls: list[str]) -> list[Product]:
        """Visit each product detail page and expand variants."""
        products: list[Product] = []
        
        # Here's where async really shines. We'll use a semaphore to limit concurrency.
        semaphore = asyncio.Semaphore(5)

        async def _fetch_and_parse(url: str) -> list[Product]:
            async with semaphore:
                try:
                    html = await self._client.fetch(url)
                    return self._provider.parse_product_detail(html)
                except Exception as exc:
                    logger.error("Failed to parse product at %s: %s", url, exc)
                    return []

        tasks = [_fetch_and_parse(url) for url in product_urls]
        results = await asyncio.gather(*tasks)
        
        for sublist in results:
            products.extend(sublist)
            
        return products
