"""Tests for Pydantic domain models — price cleaning, color normalisation, etc."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

from src.domain.models import Product, ScrapeResult
from tests.conftest import (
    COLOR_BLACK,
    COLOR_BLUE,
    COLOR_RED,
    COLOR_WHITE,
    TEST_DESC,
)


# ---------------------------------------------------------------------------
# Price validator
# ---------------------------------------------------------------------------


class TestPriceValidator:
    """Verify that the ``clean_price`` field validator works correctly."""

    def test_strips_dollar_sign(self) -> None:
        p = Product(name="X", description="d", price="$1178.19")  # type: ignore[arg-type]
        assert p.price == 1178.19

    def test_strips_euro_sign(self) -> None:
        p = Product(name="X", description="d", price="€999.00")  # type: ignore[arg-type]
        assert p.price == 999.00

    def test_strips_pound_sign(self) -> None:
        p = Product(name="X", description="d", price="£42.50")  # type: ignore[arg-type]
        assert p.price == 42.50

    def test_handles_whitespace(self) -> None:
        p = Product(name="X", description="d", price="  $  99.99  ")  # type: ignore[arg-type]
        assert p.price == 99.99

    def test_accepts_float(self) -> None:
        p = Product(name="X", description="d", price=123.45)
        assert p.price == 123.45

    def test_accepts_int(self) -> None:
        p = Product(name="X", description="d", price=100)
        assert p.price == 100.0

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse price"):
            Product(name="X", description="d", price="")  # type: ignore[arg-type]

    def test_rejects_non_numeric(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse price"):
            Product(name="X", description="d", price="free")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Color normalisation
# ---------------------------------------------------------------------------


class TestColorValidator:
    """Ensure colours are collapsed to None when not meaningful."""

    def test_none_stays_none(self) -> None:
        p = Product(name="X", description=TEST_DESC, price=10.0)
        assert p.colors is None

    def test_empty_list_becomes_none(self) -> None:
        p = Product(name="X", description=TEST_DESC, price=10.0, colors=[])
        assert p.colors is None

    def test_single_color_becomes_none(self) -> None:
        p = Product(name="X", description=TEST_DESC, price=10.0, colors=[COLOR_BLACK])
        assert p.colors is None

    def test_multiple_colors_kept(self) -> None:
        p = Product(name="X", description=TEST_DESC, price=10.0, colors=[COLOR_BLACK, COLOR_WHITE])
        assert p.colors == [COLOR_BLACK, COLOR_WHITE]

    def test_whitespace_colors_filtered(self) -> None:
        p = Product(name="X", description=TEST_DESC, price=10.0, colors=["", "  ", COLOR_RED, COLOR_BLUE])
        assert p.colors == [COLOR_RED, COLOR_BLUE]


# ---------------------------------------------------------------------------
# ScrapeResult / total calculation
# ---------------------------------------------------------------------------


class TestScrapeResult:
    """Verify that the total is computed correctly from the product list."""

    def test_total_computed_from_products(self) -> None:
        prices = [10.50, 20.25, 5.00]
        products = [
            Product(name=f"P{i}", description=TEST_DESC, price=price)
            for i, price in enumerate(prices)
        ]
        result = ScrapeResult.from_products(products)
        assert result.total == sum(prices)
        assert len(result.results) == len(prices)

    def test_empty_list_gives_zero_total(self) -> None:
        result = ScrapeResult.from_products([])
        assert result.total == 0.0
        assert result.results == []

    def test_floating_point_precision(self) -> None:
        """Ensure we round to 2 decimal places to avoid IEEE 754 drift."""
        p1_price, p2_price = 0.1, 0.2
        products = [
            Product(name="A", description=TEST_DESC, price=p1_price),
            Product(name="B", description=TEST_DESC, price=p2_price),
        ]
        result = ScrapeResult.from_products(products)
        assert result.total == round(p1_price + p2_price, 2)

    def test_serialization_structure(self) -> None:
        """The JSON shape must have 'results' and 'total' at the top level."""
        products = [Product(name="X", description=TEST_DESC, price=99.99)]
        result = ScrapeResult.from_products(products)
        data = result.model_dump()
        assert "results" in data
        assert "total" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["total"], float)
