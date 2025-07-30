<!-- Keep a Changelog: https://keepachangelog.com/en/1.0.0/ -->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v12i] - 2025-07-29
### Added
- Python logging module replaces manual logging; logs to file and console, with error log separation.
- `__version__`, `__author__`, and `__date__` metadata added to all main scripts.

### Changed
- All manual log file writes replaced with robust logging configuration.
- All logs now routed to `/logs/` directory.

### Fixed
- Environment and interpreter issues resolved for OpenCV (`cv2`) import.
- Codebase hygiene: removed duplicate/legacy functions, improved maintainability.

## [v12h] - 2025-07-28
### Fixed
- Widget reference bug causing NameError.

### Changed
- Proper widget setup before config restore.
- Version tracking to log and footer.
- Geometry logging and verbose debug mode.
- Run log structured entry/exit messages.
