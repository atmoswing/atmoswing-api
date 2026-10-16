# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.2.0 - 2026-10-16

### Upgrade notes

- The Docker image now runs as a non-root user (UID/GID 1000, configurable with the `APP_UID`/`APP_GID` build args). Grant it read access to the region directories with compose `group_add` (the GIDs of the SFTP groups, see `getent group atmoswing_<region>`), and make sure the uploaded files are group-readable.
- The cron jobs writing to the data directory (`cleaner.py`, `warmup_cache.py`) must run as root: `docker exec -u 0 ...`.
- Behind a reverse proxy, set `FORWARDED_ALLOW_IPS` to the proxy address (e.g. `172.16.0.0/12`), otherwise all clients share the same rate-limit budget. Never use `*`.
- `app.log` is no longer written to the data directory. Use the `log_file` setting to log to a file.
- `requirements.txt` is removed: all dependencies are declared in `pyproject.toml`.

### Added

- Adding a `/health` endpoint, used by a Docker `HEALTHCHECK`.
- Adding the `rate_limit` setting (per-client budget for all requests, default 600/minute).
- Adding the `log_file` setting.
- Testing on Python 3.10 to 3.14, linting with ruff, and smoke-testing the Docker image in CI.

### Changed

- Returning HTTP 400 with a clear message for invalid inputs and missing data, and a generic 500 for other errors (no internal details are exposed anymore).
- Resolving `latest` before the cache lookups, so cached results are keyed on the actual forecast date.
- Making the `latest` forecast resolution robust to stray files and empty directories.
- Replacing slowapi by the `limits` library for rate limiting.
- Configuring logging once, on the `atmoswing_api` logger only.
- Running uvicorn with `--proxy-headers`.
- Running the tests before publishing the package and the Docker image, and updating the GitHub actions.
- Defining the version only in `pyproject.toml`.
- Removing duplicated settings, prebuilt-cache and file-lookup code.

### Fixed

- Preventing path traversal through the region, method and configuration parameters.
- Fixing the rate limit, which was not applied with recent FastAPI versions.
- Fixing `/minidocs` listing no routes with recent FastAPI versions.
- Fixing the Redis client lifecycle: requests no longer fail when Redis errors.
- Fixing target dates before the forecast range being matched to the last lead time.
- Replacing an assert by a proper error when the stations of the configurations differ.
- Fixing an import error on Python 3.13 and newer.
- Adding the missing `h5py` dependency.


## 1.1.1 - 2026-09-22

### Changed

- Building the warmup cache for the most recent forecasts first.

### Fixed

- Better handling of exceptions in the cache warmup script.


## 1.1.0 - 2025-10-09

### Added

- Adding a rate limit to avoid crashing the app.
- Adding normalization of the per-config forecasts.
- Adding a json cache for heavy computations.
- Adding a cache warmup script and a cleaner script.
- Adding a method to check if forecasts are available for a certain date.
- Returning the corresponding analog dates along the values.

### Changed

- Disable CORS headers for API responses. They were causing issues with some clients. Handling CORS should be done at a higher level (e.g., API Gateway, reverse proxy).
- Returning no data when the forecast is out of range.
- Improving Redis usage.
- Refactors logging configuration into a utility.
- Changing Docker image name to 'atmoswing/web-api'.

### Fixed

- Improving logging in case of exceptions.
- Fixing an issue with parallel requests causing errors: switching to h5netcdf engine.
- Fixing Redis cache issue due to decorator misusage.
- Fixing issue with special characters.


## 1.0.4 - 2025-06-23

### Changed

- Adding CORS headers to the API responses.


## 1.0.3 - 2025-06-10

### Changed

- Refactors cleaner script to use argparse.


## 1.0.1 - 2025-06-10

### Added

- Adding a script to remove old forecasts.
- Adding a request to get the relevant entities.
- Handle lead time not matching an exact target date.
- Return the lead time in addition to the target date.
- Returning additional parameters.
- Providing more error details.

### Changed

- Removing exception details when Redis is not found.

### Fixed

- Hiding log file from regions listing.


## 1.0.0 - 2025-04-15
Initial release.
