# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog(https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning(https://semver.org/spec/v2.0.0.html).


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
