"""Base interfaces and utilities for scraper providers."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from urllib.parse import urljoin

if TYPE_CHECKING:
    from src.domain.models import Product


class BaseScraperProvider(ABC):
    """Abstract Base Class for all site-specific scrapers.
    
    Provides shared utilities for cleaning and normalizing data.
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    @property
    def base_url(self) -> str:
        """The root URL for this provider."""
        return self._base_url

    # --- Common Utilities (Shared by all scrapers) ---

    def make_absolute(self, url: str) -> str:
        """Convert a relative path to an absolute URL using the base_url."""
        if not url:
            return ""
        # urljoin handles both '/path' (root-relative) and 'path' (relative) correctly
        return urljoin(self._base_url + "/", url)

    def clean_text(self, text: str | None) -> str:
        """Strip whitespace and collapse multiple spaces/newlines."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    # --- Abstract Methods (Must be implemented by children) ---

    @abstractmethod
    def parse_subcategory_urls(self, html: str, current_url: str) -> list[str]:
        """Extract subcategory links from a page."""
        pass

    @abstractmethod
    def parse_product_urls(self, html: str, current_url: str) -> list[str]:
        """Extract product detail links from a listing page."""
        pass

    @abstractmethod
    def parse_pagination_urls(self, html: str, current_url: str) -> list[str]:
        """Extract additional pagination links from a listing page."""
        pass

    @abstractmethod
    def parse_product_detail(self, html: str) -> list[Product]:
        """Extract products/variants from a detail page."""
        pass
