"""Base interface for product exporters."""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from src.domain.models import ScrapeResult


class Exporter(Protocol):
    """Protocol for exporting scrape results to different formats."""

    def export(self, result: ScrapeResult, target: Path | None = None) -> str:
        """Export the result and return a string representation (or success message)."""
        ...
