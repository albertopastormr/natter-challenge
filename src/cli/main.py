"""CLI entry point for the Natter scraper."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer

from src.services.scraper import scrape_site
from src.exporters.implementations import get_exporter

app = typer.Typer(
    help="Crawl target sites and output structured product data.",
    add_completion=False,
    no_args_is_help=True,
)

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Show the application version."""
    typer.echo("Natter Scrapper v1.0.0")


@app.command()
def scrape(
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Write results to this file instead of stdout.",
            dir_okay=False,
        ),
    ] = None,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: json or csv.",
        ),
    ] = "json",
    timeout: Annotated[
        float,
        typer.Option(
            "--timeout",
            "-t",
            help="HTTP request timeout in seconds.",
        ),
    ] = 30.0,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """Crawl the target site and output structured product data."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        # Run the async orchestration
        result = asyncio.run(scrape_site(timeout=timeout))

        # Select exporter
        exporter = get_exporter(format)
        
        # Export and display
        out_message = exporter.export(result, target=output)
        
        if output:
            typer.echo(typer.style(out_message, fg=typer.colors.GREEN))
        else:
            typer.echo(out_message)

    except Exception as exc:
        typer.echo(typer.style(f"Error: {exc}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
