"""Tests for the HTML parser (WebScraperIoProvider)."""

from __future__ import annotations
import pytest

pytestmark = pytest.mark.unit

from src.scrapers.parser import WebScraperIoProvider
from tests.conftest import (
    CAT_COMPUTERS,
    CAT_LAPTOPS,
    CAT_PHONES,
    CAT_TABLETS,
    CAT_TOUCH,
    P31_DESC,
    P31_ID,
    P31_NAME,
    P31_PRICE,
    P32_COLORS,
    P32_DESC,
    P32_ID,
    P32_NAME,
    P32_PRICE,
    P32_VARIANTS,
)

BASE = "https://webscraper.io/test-sites/e-commerce/static"


@pytest.fixture
def provider() -> WebScraperIoProvider:
    return WebScraperIoProvider()


# ---------------------------------------------------------------------------
# Subcategory discovery
# ---------------------------------------------------------------------------


class TestParseSubcategoryUrls:
    def test_finds_subcategories(self, provider: WebScraperIoProvider, homepage_html: str) -> None:
        urls = provider.parse_subcategory_urls(homepage_html, BASE)
        assert f"{BASE}/{CAT_LAPTOPS}" in urls
        assert f"{BASE}/{CAT_TABLETS}" in urls
        assert f"{BASE}/{CAT_TOUCH}" in urls

    def test_includes_parent_categories(self, provider: WebScraperIoProvider, homepage_html: str) -> None:
        urls = provider.parse_subcategory_urls(homepage_html, BASE)
        assert f"{BASE}/{CAT_COMPUTERS}" in urls
        assert f"{BASE}/{CAT_PHONES}" in urls


# ---------------------------------------------------------------------------
# Product links
# ---------------------------------------------------------------------------


class TestParseProductUrls:
    def test_extracts_product_links(self, provider: WebScraperIoProvider, listing_page_html: str) -> None:
        urls = provider.parse_product_urls(listing_page_html, BASE)
        assert len(urls) == 2
        assert f"{BASE}/product/{P31_ID}" in urls
        assert f"{BASE}/product/{P32_ID}" in urls

    def test_empty_page(self, provider: WebScraperIoProvider) -> None:
        urls = provider.parse_product_urls("<html></html>", BASE)
        assert urls == []


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class TestParsePaginationUrls:
    def test_extracts_pagination_links(self, provider: WebScraperIoProvider, listing_page_html: str) -> None:
        urls = provider.parse_pagination_urls(listing_page_html, BASE)
        assert f"{BASE}/computers/laptops?page=2" in urls

    def test_no_pagination(self, provider: WebScraperIoProvider) -> None:
        html = "<html><body></body></html>"
        urls = provider.parse_pagination_urls(html, BASE)
        assert urls == []


# ---------------------------------------------------------------------------
# Product Detail (1:N Expansion)
# ---------------------------------------------------------------------------


class TestParseProductDetail:
    def test_simple_product_returns_single_item(
        self, provider: WebScraperIoProvider, product_no_variants_html: str
    ) -> None:
        products = provider.parse_product_detail(product_no_variants_html)
        assert len(products) == 1
        p = products[0]
        assert p.name == P31_NAME
        assert p.price == P31_PRICE
        assert p.description == P31_DESC
        assert p.colors is None

    def test_three_variants_produce_three_products(
        self, provider: WebScraperIoProvider, product_with_variants_html: str
    ) -> None:
        products = provider.parse_product_detail(product_with_variants_html)
        assert len(products) == len(P32_VARIANTS)

    def test_variant_names_include_swatch_label(
        self, provider: WebScraperIoProvider, product_with_variants_html: str
    ) -> None:
        products = provider.parse_product_detail(product_with_variants_html)
        names = [p.name for p in products]
        for swatch in P32_VARIANTS:
            assert f"{P32_NAME} HDD: {swatch}" in names

    def test_variant_prices_increment_by_20(
        self, provider: WebScraperIoProvider, product_with_variants_html: str
    ) -> None:
        products = provider.parse_product_detail(product_with_variants_html)
        for i, product in enumerate(products):
            expected_price = round(P32_PRICE + i * provider.SWATCH_PRICE_STEP, 2)
            assert product.price == expected_price

    def test_variants_share_description(
        self, provider: WebScraperIoProvider, product_with_variants_html: str
    ) -> None:
        products = provider.parse_product_detail(product_with_variants_html)
        for product in products:
            assert product.description == P32_DESC

    def test_variants_share_colors(
        self, provider: WebScraperIoProvider, product_with_variants_html: str
    ) -> None:
        products = provider.parse_product_detail(product_with_variants_html)
        for product in products:
            assert product.colors == P32_COLORS

    def test_single_color_becomes_none(
        self, provider: WebScraperIoProvider, product_single_color_html: str
    ) -> None:
        products = provider.parse_product_detail(product_single_color_html)
        for product in products:
            assert product.colors is None

    def test_missing_price_raises(self, provider: WebScraperIoProvider) -> None:
        html = "<html><body><div class='caption'><h4>No price here</h4></div></body></html>"
        with pytest.raises(ValueError, match="Price element not found"):
            provider.parse_product_detail(html)

    def test_missing_name_uses_fallback(self, provider: WebScraperIoProvider) -> None:
        html = "<html><body><h4 class='price'>$10</h4></body></html>"
        products = provider.parse_product_detail(html)
        assert products[0].name == provider.NAME_FALLBACK

    def test_missing_description_is_empty_string(self, provider: WebScraperIoProvider) -> None:
        html = "<html><body><h4 class='title'>N</h4><h4 class='price'>$10</h4></body></html>"
        products = provider.parse_product_detail(html)
        assert products[0].description == ""
