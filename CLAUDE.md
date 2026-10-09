# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

FastAPI web service that serves AtmoSwing analog-method forecasts (NetCDF files) as JSON. Python >= 3.10 (CI tests 3.10–3.12; Docker uses 3.12).

## Commands

```bash
pip install -e ".[test]"                                # runtime + test dependencies (all in pyproject.toml)
uvicorn atmoswing_api.app.main:app --reload              # dev server
pytest                                                   # all tests (asyncio_mode=auto via pytest.ini)
pytest tests/test_routes_forecasts.py::test_analog_dates # single test
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics   # CI's blocking lint check
```

Configuration comes from env / `.env` via `atmoswing_api/config.py` (`data_dir`, `debug`). Redis is optional: `REDIS_HOST`/`REDIS_PORT` (default localhost:6379); without it, caching is silently bypassed.

API docs at `/docs`, `/redoc`, `/minidocs` (custom template `templates/api_doc.html`), `/openapi.json`.

## Architecture

**Layering:** `app/routes/*` (FastAPI routers, mounted under `/meta`, `/forecasts`, `/aggregations` in `app/main.py`) → `app/services/*` → `app/utils/utils.py` (file discovery, date/lead-time math, NetCDF indexing). Response schemas are in `app/models/models.py`.

**Service pattern:** each service exposes an `async def get_x(data_dir, region, ...)` that just does `asyncio.to_thread(_get_x, ...)`; the synchronous `_get_x` does the blocking xarray/NetCDF work. Add new endpoints following this pair pattern. Every service accepts `forecast_date == "latest"`, resolved via `utils.get_last_forecast_date`.

**Route pattern:** routes inject `config.Settings` through an `lru_cache`d `get_settings` dependency and call services through a `_handle_request` helper that maps `FileNotFoundError` → HTTP 400 and other errors → 500. Routes are decorated `@router.get` → `@resolve_latest` → `@redis_cache(ttl=...)`, in that order. `resolve_latest` (`routes/common.py`) turns `forecast_date` into its canonical `YYYY-MM-DDTHH` form and resolves `latest` (reused for 10 s), so the Redis and prebuilt caches never key on `latest`. `redis_cache` (`atmoswing_api/cache.py`) keys on function name + args and backs off for 5 s whenever Redis errors.

**Data layout:** `{data_dir}/{region}/YYYY/MM/DD/YYYY-MM-DD_HH.<method>.<config>.nc` (region dirs may be symlinks; see `check_region_path`). `tests/data/` holds real sample forecasts for regions `adn` and `zap`.

**Prebuilt cache (two-tier caching):** `scripts/warmup_cache.py` (run externally, e.g. cron) precomputes heavy aggregation/meta results into `{data_dir}/.prebuilt_cache/` as JSON, regenerating when source `.nc` mtimes are newer; it uses a cross-platform singleton file lock. `routes/aggregations.py::load_prebuilt_result` checks these files first before computing. Both sides must use `utils.compute_cache_hash` / `utils.make_cache_paths` with identical parameters, so keep them in sync when changing endpoint arguments.

**Other scripts:** `scripts/cleaner.py --data-dir ... --keep-days 60` deletes old forecasts; `scripts/export_docs.py` exports the API docs.

**App-level:** `main.py` sets up slowapi rate limiting (120/min per IP), a custom 404 message, and a global 500 handler. CORS middleware is intentionally disabled.

## Testing

Route tests use `TestClient` and override the routes' `get_settings` dependency (`app.dependency_overrides[...]`) to point `data_dir` at `tests/data`. Each router module has its own `get_settings`, so override the one from the module under test.

## Release

Version lives in both `pyproject.toml` and `atmoswing_api/__version__.py`; update both and `CHANGELOG.md`. GitHub workflows publish to PyPI and build the `atmoswing/web-api` Docker image.
