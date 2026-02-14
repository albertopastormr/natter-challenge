"""Scraper service orchestration (Async)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.scrapers.client import HttpClient
from src.scrapers.crawler import Crawler
from src.services.aggregator import aggregate
from src.scrapers.parser import WebScraperIoProvider

if TYPE_CHECKING:
    from src.domain.models import ScrapeResult
    from src.scrapers.base import BaseScraperProvider

__all__ = ["scrape_site", "DEFAULT_BASE_URL", "get_provider"]

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://webscraper.io/test-sites/e-commerce/static"


def get_provider(url: str) -> BaseScraperProvider:
    """Simple Factory/Registry to pick a provider based on the URL.
    
    This is what makes the system 'multi-site ready'. 
    To add a new site, add its URL pattern here.
    """
    if "webscraper.io" in url:
        return WebScraperIoProvider()
        
    # Example placeholder for interview extension:
    # if "amazon.com" in url:
    #     return AmazonProvider()
        
    raise ValueError(f"No scraper provider registered for URL: {url}")


async def scrape_site(
    provider: BaseScraperProvider | None = None,
    timeout: float = 30.0,
) -> ScrapeResult:
    """Orchestrate the full async scraping process.
    
    Accepts a 'provider' to allow multi-site support. Defaults to WebScraperIoProvider.
    """
    provider = provider or WebScraperIoProvider()
    
    logger.info("Initializing async scrape for %s", provider.base_url)

    async with HttpClient(timeout=timeout) as client:
        crawler = Crawler(client=client, provider=provider)
        products = await crawler.crawl()

    return aggregate(products)
