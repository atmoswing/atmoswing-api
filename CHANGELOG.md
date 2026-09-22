# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog(https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning(https://semver.org/spec/v2.0.0.html).

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
