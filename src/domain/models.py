"""Domain models for scraped product data.

All data validation and cleaning is centralized here via Pydantic validators,
keeping the scraper logic free of formatting concerns.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, field_validator


class Product(BaseModel):
    """A single product entry (one per variant)."""

    name: str
    description: str
    price: float
    colors: list[str] | None = None

    @field_validator("price", mode="before")
    @classmethod
    def clean_price(cls, value: object) -> float:
        """Strip currency symbols and whitespace, then convert to float.

        Handles formats like '$1178.19', '€999.00', or already-numeric values.
        """
        if isinstance(value, (int, float)):
            return float(value)

        raw = str(value).strip()
        cleaned = re.sub(r"[^\d.]", "", raw)
        if not cleaned:
            raise ValueError(f"Cannot parse price from: {value!r}")
        return float(cleaned)

    @field_validator("colors", mode="before")
    @classmethod
    def normalize_colors(cls, value: object) -> list[str] | None:
        """Return None unless the product genuinely has multiple color options."""
        if value is None:
            return None
        if not isinstance(value, list):
            return None
        # Filter out empty strings and placeholder values
        filtered = [c.strip() for c in value if c and c.strip()]
        if len(filtered) <= 1:
            return None
        return filtered


class ScrapeResult(BaseModel):
    """Final output envelope containing all products and a price total."""

    results: list[Product]
    total: float

    @classmethod
    def from_products(cls, products: list[Product]) -> ScrapeResult:
        """Create a ScrapeResult from a list of products, auto-calculating the total."""
        total = round(sum(p.price for p in products), 2)
        return cls(results=products, total=total)
