# 2026-04-15 Implementation Audit

## Status

All items from the 2026-04-15 audit remediation plan are now implemented in the codebase.

## Implemented Changes

- Scraper loading and runtime safety
  - Selenium scraper imports are optional in `scrapers/__init__.py`.
  - `monitor_engine.py` distinguishes dependency-unavailable engine initialization from ordinary scrape failures.
  - regression coverage includes Playwright-only import safety without `selenium`.
- Joonggonara search and detail enrichment
  - Naver result parsing now accepts only Joonggonara article links with numeric `articleid` values.
  - known noise anchors are rejected before item creation.
  - enrichment waits for `iframe#cafe_main` and extracts seller/location/price/title from frame content with outer-page fallback only if needed.
- Bunjang detail enrichment and sale status plumbing
  - detail enrichment is API-first and uses the Bunjang product-detail API for seller/location/price/sale status.
  - seller fallback selectors were updated to the current `/shop/.../products` structure.
  - `models.Item` now carries `sale_status`.
  - database writes prefer explicit scraper-provided sale status over title heuristics.
- Danggeun and Bunjang observability
  - per-search candidate counters and drop-reason summaries are logged.
  - Playwright writes anomaly diagnostics into `debug_output/` when candidate DOM/data exists but parsed results still end at zero.
- Filter and enrichment flow
  - enrichment now uses a two-phase shared budget per platform per keyword per cycle.
  - prefilter enrichment is targeted to location-filter and blocked-seller decisions.
  - remaining budget is spent on kept items that still need seller/location for persistence and notifications.
- Tests and fixtures
  - live-markup fixtures were added for Danggeun, Bunjang, and Joonggonara.
  - regression tests cover parser behavior, import safety, DB sale-status precedence, and targeted enrichment flow.
- Packaging and docs
  - `used_market_notifier.spec` now collects the `aiohttp` dependency tree used by Bunjang detail enrichment.
  - `README.md`, `claude.md`, and `gemini.md` were aligned to the 2026-04 implementation baseline.

## Verification

- Unit regression:
  - `python -m unittest discover -s tests -q`
  - baseline: `Ran 57 tests` / `OK`
- Smoke checks completed during implementation:
  - Danggeun search for `아이폰`: non-zero results confirmed
  - Bunjang search for `아이폰`: non-zero results confirmed
  - Joonggonara search for `아이폰`: non-zero results confirmed
  - Bunjang detail enrichment: seller/location/status populated from API
  - Joonggonara detail enrichment: iframe-based seller/price extraction confirmed
