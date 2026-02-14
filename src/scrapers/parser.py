"""Provider for WebScraper.io test site."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from src.domain.models import Product
from src.scrapers.base import BaseScraperProvider

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class WebScraperIoProvider(BaseScraperProvider):
    """Implementation of BaseScraperProvider for the WebScraper.io test site."""

    def __init__(self) -> None:
        # We pass the default URL to the base class
        super().__init__("https://webscraper.io/test-sites/e-commerce/static")

    # ---------------------------------------------------------------------------
    # Schema / Selectors
    # ---------------------------------------------------------------------------

    SIDEBAR = ".sidebar-nav, #side-menu, .category-link"
    LINK_WITH_HREF = "a[href]"
    STATIC_URL_MARKER = "/test-sites/e-commerce/static/"
    PATH_PART_STATIC = "static"

    PRODUCT_LINK = "a.title[href]"
    PAGINATION_LINK = "ul.pagination a.page-link[href]"

    NAME_PRIMARY = ".caption h4.title"
    NAME_SECONDARY = ".caption h4:nth-of-type(2)"
    NAME_CARD = "h4.card-title"
    NAME_FALLBACK = "Unknown"
    DESCRIPTION = "p.description"
    PRICE = "h4.price"
    
    COLOR_SELECT = 'select[aria-label="color"]'
    COLOR_OPTION = "option"
    COLOR_PLACEHOLDER = "select color"
    
    SWATCH_CONTAINER = ".swatches"
    SWATCH_BTN = "button.swatch"
    VARIANT_LABEL = "label"

    SWATCH_PRICE_STEP = 20.0

    # ---------------------------------------------------------------------------
    # Public API Implementation
    # ---------------------------------------------------------------------------

    def parse_subcategory_urls(self, html: str, current_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        sidebar = soup.select_one(self.SIDEBAR)
        container: BeautifulSoup | Tag = sidebar if sidebar else soup

        urls: list[str] = []
        for anchor in container.select(self.LINK_WITH_HREF):
            href = str(anchor.get("href", ""))
            if self.STATIC_URL_MARKER in href:
                path = urlparse(href).path
                parts = [p for p in path.split("/") if p]
                if self.PATH_PART_STATIC in parts:
                    static_idx = parts.index(self.PATH_PART_STATIC)
                    if len(parts) > static_idx + 1:
                        # Use our new utility from BaseScraperProvider
                        full_url = self.make_absolute(href)
                        if full_url not in urls:
                            urls.append(full_url)
        return urls

    def parse_product_urls(self, html: str, current_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        for anchor in soup.select(self.PRODUCT_LINK):
            href = str(anchor.get("href", ""))
            full_url = self.make_absolute(href)
            if full_url not in urls:
                urls.append(full_url)
        return urls

    def parse_pagination_urls(self, html: str, current_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        for link in soup.select(self.PAGINATION_LINK):
            href = str(link.get("href", ""))
            full_url = self.make_absolute(href)
            if full_url not in urls:
                urls.append(full_url)
        return urls

    def parse_product_detail(self, html: str) -> list[Product]:
        soup = BeautifulSoup(html, "lxml")
        name = self._extract_name(soup)
        description = self._extract_description(soup)
        base_price = self._extract_base_price(soup)
        colors = self._extract_colors(soup)
        variant_label, swatches = self._extract_variants(soup)

        if not swatches:
            return [
                Product(name=name, description=description, price=base_price, colors=colors)
            ]

        products: list[Product] = []
        for index, swatch_value in enumerate(swatches):
            variant_price = round(base_price + index * self.SWATCH_PRICE_STEP, 2)
            display_label = f"{variant_label} " if variant_label else ""
            variant_name = f"{name} {display_label}{swatch_value}".strip()
            products.append(
                Product(name=variant_name, description=description, price=variant_price, colors=colors)
            )
        return products

    # ---------------------------------------------------------------------------
    # Private UI Extraction Helpers
    # ---------------------------------------------------------------------------

    def _extract_name(self, soup: BeautifulSoup) -> str:
        name_el = (
            soup.select_one(self.NAME_PRIMARY) 
            or soup.select_one(self.NAME_SECONDARY)
            or soup.select_one(self.NAME_CARD)
        )
        return name_el.get_text(strip=True) if name_el else self.NAME_FALLBACK

    def _extract_description(self, soup: BeautifulSoup) -> str:
        desc_el = soup.select_one(self.DESCRIPTION)
        # Use our new clean_text utility
        return self.clean_text(desc_el.get_text()) if desc_el else ""

    def _extract_base_price(self, soup: BeautifulSoup) -> float:
        price_el = soup.select_one(self.PRICE)
        if price_el is None:
            raise ValueError("Price element not found")
        return Product.clean_price(price_el.get_text(strip=True))

    def _extract_colors(self, soup: BeautifulSoup) -> list[str] | None:
        select = soup.select_one(self.COLOR_SELECT)
        if select is None: return None
        colors = [
            self.clean_text(opt.get_text()) for opt in select.select(self.COLOR_OPTION)
            if opt.get_text(strip=True) and opt.get_text(strip=True).lower() != self.COLOR_PLACEHOLDER
        ]
        return colors if colors else None

    def _extract_variants(self, soup: BeautifulSoup) -> tuple[str | None, list[str]]:
        container = soup.select_one(self.SWATCH_CONTAINER)
        if not container: return None, []
        label_el = container.select_one(self.VARIANT_LABEL) or container.find_previous_sibling(self.VARIANT_LABEL)
        label = label_el.get_text(strip=True) if label_el else None
        values = [btn.get_text(strip=True) for btn in container.select(self.SWATCH_BTN) if btn.get_text(strip=True)]
        return label, values
