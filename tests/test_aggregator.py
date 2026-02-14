"""Tests for the aggregation service."""

from __future__ import annotations

import pytest
from src.domain.models import Product
from src.services.aggregator import aggregate

pytestmark = pytest.mark.unit
from tests.conftest import (
    TEST_DESC,
    TEST_PRICE_1,
    TEST_PRICE_2,
    TEST_PRICE_3,
    TEST_PRICE_4,
    TEST_PRICE_TOTAL,
)


class TestAggregate:
    def test_computes_total(self) -> None:
        products = [
            Product(name="A", description=TEST_DESC, price=TEST_PRICE_1),
            Product(name="B", description=TEST_DESC, price=TEST_PRICE_2),
        ]
        result = aggregate(products)
        assert result.total == TEST_PRICE_TOTAL
        assert len(result.results) == len(products)

    def test_empty_list(self) -> None:
        result = aggregate([])
        assert result.total == 0.0
        assert result.results == []

    def test_single_product(self) -> None:
        products = [Product(name="Solo", description=TEST_DESC, price=TEST_PRICE_3)]
        result = aggregate(products)
        assert result.total == TEST_PRICE_3

    def test_result_is_serializable(self) -> None:
        products = [Product(name="X", description=TEST_DESC, price=TEST_PRICE_4)]
        result = aggregate(products)
        data = result.model_dump()
        assert data["total"] == TEST_PRICE_4
        assert len(data["results"]) == len(products)
