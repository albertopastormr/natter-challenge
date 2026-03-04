# Natter — E-Commerce Product Scraper

An async CLI application that extracts structured product data, handling pagination, dynamic attribute variants (swatches), and color normalization.

---

## Architecture & Design Decisions

This project is built using **SOLID principles** to ensure that extending the scraper for new websites or features is a matter of configuration.

### 1. Multi-Site Readiness (Provider Pattern)
Instead of a hardcoded scraper, I used a **Provider Pattern**. All site-specific logic (selectors, URL patterns, variant extraction) is isolated in a `Provider` class.
- **ScraperProvider (Protocol)**: Defines the contract.
- **WebScraperIoProvider (Implementation)**: Contains the logic for the target test site.
- **Benefit**: To support a new site like a real e-commerce site, you simply implement a new `ScraperProvider` and plug it in.

### 2. The "Async" Jump (High Concurrency)
I/O is the bottleneck in scraping. The codebase is fully **async/await** from the ground up using `httpx.AsyncClient` and `asyncio`.
- **Concurrency Control**: Uses `asyncio.Semaphore` to bound the number of concurrent connections, avoiding IP bans while maximizing throughput.
- **Performance**: Extraction speed is orders of magnitude faster than synchronous implementations.

### 3. Pluggable Exporters
Output handling is decoupled from the CLI logic.
- **Exporter Protocol**: Defines how data should be formatted.
- **Flexible Output**: Supports **JSON** and **CSV** out of the box.
- **Command**: `uv run natter scrape --format csv`

### 4. Service-Oriented Orchestration
The CLI acts as a thin wrapper around a **Service Layer** (`src/services/scraper.py`). This service orchestrates the `HttpClient`, `Crawler`, and `Provider`, making the core logic easily embeddable in other applications (like a web API or a scheduled task).

---

## Technical Stack
- **Python 3.12+**
- **uv**: Dependency & Environment Management.
- **Pydantic v2**: Data validation and serialization.
- **HTTPX (Async)**: Modern async HTTP client.
- **BeautifulSoup4 + lxml**: Parsing infrastructure.
- **Pytest + AnyIO**: Async-aware testing.

---

## Quick Start

### 1. Environment Setup
```bash
uv sync
```

### 2. Execution
```bash
# Default JSON output to stdout
uv run natter scrape

# Export to CSV file
uv run natter scrape --output products.csv --format csv

# Verbose mode
uv run natter scrape -v
```

### 3. Quality Control
```bash
# Run unit tests (fast, no network)
uv run pytest -v -m unit

# Run integration tests (hits the live site)
uv run pytest -v -m integration

# Static type check
uv run mypy src tests
```

---

## Output Format Example (JSON)

```json
{
  "results": [
    {
      "name": "Packard 255 G2 HDD: 128",
      "description": "15.6\", AMD E1-1200 1.4GHz, 4GB, 500GB",
      "price": 416.99,
      "colors": ["Gold", "Silver"]
    }
  ],
  "total": 416.99
}
```
