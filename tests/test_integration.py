"""Integration tests hitting the live test site."""

from __future__ import annotations
import pytest
from src.services.scraper import scrape_site
from src.domain.models import ScrapeResult

pytestmark = pytest.mark.anyio


@pytest.mark.integration
async def test_full_scrape_integration() -> None:
    """Perform a real crawl of the test site.
    
    We expect:
    1. A successful ScrapeResult object.
    2. At least some products (the site has dozens).
    3. A positive total price.
    4. Variants to be correctly expanded (checked by looking for 'HDD:' in some names).
    """
    # Use a slightly longer timeout for live network
    result = await scrape_site(timeout=60.0)
    
    assert isinstance(result, ScrapeResult)
    assert len(result.results) > 0
    assert result.total > 0
    
    # Check for variant expansion in the live data
    # (Computers/Laptops usually have HDD variants)
    variant_names = [p.name for p in result.results if "HDD:" in p.name]
    assert len(variant_names) > 0, f"No variants discovered in live scrape. Total products: {len(result.results)}"
    
    # Check that prices are non-zero
    for product in result.results:
        assert product.price > 0
        assert product.name != "Unknown"
