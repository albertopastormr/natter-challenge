"""Concrete exporter implementations."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.models import ScrapeResult


class JsonExporter:
    """Exports results as formatted JSON."""

    def export(self, result: ScrapeResult, target: Path | None = None) -> str:
        json_data = result.model_dump_json(indent=2)
        if target:
            target.write_text(json_data, encoding="utf-8")
            return f"Results written to {target}"
        return json_data


class CsvExporter:
    """Exports results as CSV."""

    def export(self, result: ScrapeResult, target: Path | None = None) -> str:
        output = io.StringIO()
        fieldnames = ["name", "price", "description", "colors"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for p in result.results:
            writer.writerow({
                "name": p.name,
                "price": p.price,
                "description": p.description,
                "colors": ", ".join(p.colors) if p.colors else ""
            })
            
        csv_data = output.getvalue()
        if target:
            target.write_text(csv_data, encoding="utf-8")
            return f"Results written to {target}"
        return csv_data
