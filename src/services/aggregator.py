"""Result aggregation service.

Keeps the "calculation" concern separate from the "extraction" concern.
The total is computed only once, after all products have been collected.
"""

from __future__ import annotations

from src.domain.models import Product, ScrapeResult


def aggregate(products: list[Product]) -> ScrapeResult:
    """Build the final output envelope from a complete product list.

    This is intentionally thin — it's a named entry-point so the caller
    doesn't need to know about internal model factories.
    """
    return ScrapeResult.from_products(products)
