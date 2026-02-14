"""Shared test fixtures — sample HTML fragments for deterministic testing.

These fixtures let us test the parser without hitting the live site,
and verify the variant-expansion logic in isolation.
"""

from __future__ import annotations

import pytest

# For an actual service that we don't control, we can't predict the exact
# HTML structure, so we use a more generic fixture.
# I would build a generator for this, but I don't want to overcomplicate
# the test suite.


# ---------------------------------------------------------------------------
# Test constants (Source of truth for expected values)
# ---------------------------------------------------------------------------

# Product 31 (Simple)
P31_ID = "31"
P31_NAME = "Packard 255 G2"
P31_PRICE = 416.99
P31_DESC = '15.6", AMD E2-3800 1.3GHz, 4GB, 500GB, Windows 8.1'

# Product 32 (Variants)
P32_ID = "32"
P32_NAME = "Inspiron 15"
P32_PRICE = 745.99
P32_DESC = "Moon Silver, 15.6\", Core i7-4510U, 8GB, 1TB"
P32_VARIANTS = ["128", "256", "512"]
P32_COLORS = ["Moon Silver", "Black", "White"]

# Product Single Color
PSC_NAME = "ThinkPad X240"
PSC_PRICE = 899.99
PSC_VARIANTS = ["128", "256"]
PSC_COLORS = ["Black"]

# Generic Test Values
TEST_DESC = "d"
TEST_PRICE_1 = 100.00
TEST_PRICE_2 = 200.50
TEST_PRICE_TOTAL = 300.50
TEST_PRICE_3 = 42.00
TEST_PRICE_4 = 9.99

# Colors
COLOR_BLACK = "Black"
COLOR_WHITE = "White"
COLOR_RED = "Red"
COLOR_BLUE = "Blue"

# Subcategory discovery base
BASE_URL = "https://webscraper.io/test-sites/e-commerce/static"

# Categories
CAT_COMPUTERS = "computers"
CAT_LAPTOPS = "computers/laptops"
CAT_TABLETS = "computers/tablets"
CAT_PHONES = "phones"
CAT_TOUCH = "phones/touch"

# ---------------------------------------------------------------------------
# Listing page with 2 products and pagination
# ---------------------------------------------------------------------------

LISTING_PAGE_HTML = f"""\\
<!DOCTYPE html>
<html>
<head><title>Laptops</title></head>
<body>
<div class="sidebar-nav" id="side-menu">
  <ul>
    <li><a href="/test-sites/e-commerce/static/{CAT_COMPUTERS}">Computers</a></li>
    <li><a href="/test-sites/e-commerce/static/{CAT_LAPTOPS}">Laptops</a></li>
    <li><a href="/test-sites/e-commerce/static/{CAT_TABLETS}">Tablets</a></li>
    <li><a href="/test-sites/e-commerce/static/{CAT_PHONES}">Phones</a></li>
    <li><a href="/test-sites/e-commerce/static/{CAT_TOUCH}">Touch</a></li>
  </ul>
</div>
<div class="container">
  <div class="row">
    <div class="col-md-4">
      <div class="thumbnail">
        <div class="product-wrapper card-body">
          <div class="caption">
            <h4 class="price float-end card-title pull-right">${P31_PRICE}</h4>
            <h4><a href="/test-sites/e-commerce/static/product/{P31_ID}" class="title" title="{P31_NAME}">{P31_NAME}</a></h4>
            <p class="description card-text">{P31_DESC}</p>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="thumbnail">
        <div class="product-wrapper card-body">
          <div class="caption">
            <h4 class="price float-end card-title pull-right">${P32_PRICE}</h4>
            <h4><a href="/test-sites/e-commerce/static/product/{P32_ID}" class="title" title="{P32_NAME}">{P32_NAME}</a></h4>
            <p class="description card-text">{P32_DESC}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <ul class="pagination">
    <li class="page-item active"><a class="page-link" href="/test-sites/e-commerce/static/computers/laptops?page=1">1</a></li>
    <li class="page-item"><a class="page-link" href="/test-sites/e-commerce/static/computers/laptops?page=2">2</a></li>
    <li class="page-item"><a class="page-link" href="/test-sites/e-commerce/static/computers/laptops?page=3">3</a></li>
  </ul>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Product detail page WITHOUT variants (simple case)
# ---------------------------------------------------------------------------

PRODUCT_DETAIL_NO_VARIANTS = f"""\\
<!DOCTYPE html>
<html>
<head><title>{P31_NAME}</title></head>
<body>
<div class="container">
  <div class="product-wrapper card-body">
    <div class="caption">
      <h4 class="price float-end pull-right" itemprop="offers">
        <span itemprop="price">${P31_PRICE}</span>
      </h4>
      <h4 class="title card-title" itemprop="name">{P31_NAME}</h4>
      <p class="description card-text" itemprop="description">
        {P31_DESC}
      </p>
    </div>
  </div>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Product detail page WITH 3 HDD variants (the 1:N case)
# ---------------------------------------------------------------------------

PRODUCT_DETAIL_WITH_VARIANTS = f"""\\
<!DOCTYPE html>
<html>
<head><title>{P32_NAME}</title></head>
<body>
<div class="container">
  <div class="product-wrapper card-body">
    <div class="caption">
      <h4 class="price float-end pull-right" itemprop="offers">
        <span itemprop="price">${P32_PRICE}</span>
      </h4>
      <h4 class="title card-title" itemprop="name">{P32_NAME}</h4>
      <p class="description card-text" itemprop="description">
        {P32_DESC}
      </p>
    </div>
    <div class="swatches">
      <label>HDD:</label>
      <button class="btn swatch" value="{P32_VARIANTS[0]}">{P32_VARIANTS[0]}</button>
      <button class="btn swatch" value="{P32_VARIANTS[1]}">{P32_VARIANTS[1]}</button>
      <button class="btn swatch" value="{P32_VARIANTS[2]}">{P32_VARIANTS[2]}</button>
    </div>
    <select aria-label="color">
      <option>Select color</option>
      <option>{P32_COLORS[0]}</option>
      <option>{P32_COLORS[1]}</option>
      <option>{P32_COLORS[2]}</option>
    </select>
  </div>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Product detail page WITH swatches but only 1 color
# ---------------------------------------------------------------------------

PRODUCT_DETAIL_SINGLE_COLOR = f"""\\
<!DOCTYPE html>
<html>
<head><title>{PSC_NAME}</title></head>
<body>
<div class="container">
  <div class="product-wrapper card-body">
    <div class="caption">
      <h4 class="price float-end pull-right" itemprop="offers">
        <span itemprop="price">${PSC_PRICE}</span>
      </h4>
      <h4 class="title card-title" itemprop="name">{PSC_NAME}</h4>
      <p class="description card-text" itemprop="description">
        12.5", Core i5-4300U, 8GB, 180GB SSD
      </p>
    </div>
    <div class="swatches">
      <button class="btn swatch" value="{PSC_VARIANTS[0]}">{PSC_VARIANTS[0]}</button>
      <button class="btn swatch" value="{PSC_VARIANTS[1]}">{PSC_VARIANTS[1]}</button>
    </div>
    <select aria-label="color">
      <option>Select color</option>
      <option>{PSC_COLORS[0]}</option>
    </select>
  </div>
</div>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Homepage (for subcategory discovery)
# ---------------------------------------------------------------------------

HOMEPAGE_HTML = f"""\\
<!DOCTYPE html>
<html>
<head><title>E-commerce</title></head>
<body>
<div class="sidebar-nav" id="side-menu">
  <ul>
    <li><a href="/test-sites/e-commerce/static/{CAT_COMPUTERS}">Computers</a></li>
    <li><a href="/test-sites/e-commerce/static/{CAT_LAPTOPS}">Laptops</a></li>
    <li><a href="/test-sites/e-commerce/static/{CAT_TABLETS}">Tablets</a></li>
    <li><a href="/test-sites/e-commerce/static/{CAT_PHONES}">Phones</a></li>
    <li><a href="/test-sites/e-commerce/static/{CAT_TOUCH}">Touch</a></li>
  </ul>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Expose as pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def listing_page_html() -> str:
    return LISTING_PAGE_HTML


@pytest.fixture
def product_no_variants_html() -> str:
    return PRODUCT_DETAIL_NO_VARIANTS


@pytest.fixture
def product_with_variants_html() -> str:
    return PRODUCT_DETAIL_WITH_VARIANTS


@pytest.fixture
def product_single_color_html() -> str:
    return PRODUCT_DETAIL_SINGLE_COLOR


@pytest.fixture
def homepage_html() -> str:
    return HOMEPAGE_HTML
