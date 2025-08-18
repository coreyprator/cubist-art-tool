<!-- Keep a Changelog: https://keepachangelog.com/en/1.0.0/ -->
# Changelog

All notable changes to this project will be documented in this file.

 # Changelog

## [v1.0.0] - 2025-08-18
### Added
- Deterministic point sampling via `--seed` across PNG and SVG.
- SVG export uses the exact same points/geometry as raster (PNG), fixing misalignment.
- CLI `METRICS:` line for machine-readable run stats (mode, requested/sampled/corners/total points, shape counts, file paths).
- Lightweight SVG parity validator hook in `test_cli.py` (counts polygons/paths, compares to raster shape count).
- Friendly early-exit for archive-only runs and clearer error messages.

### Fixed
- Intermittent point-count mismatches between PNG/SVG.
- Rectangles mode honoring grid-based counts (and clarifying `--points` behavior).
- Multiple indentation/merge artifacts; removed duplicate `if __name__ == "__main__":` blocks.

### Known
- Cascade mode deferred to next release.
- SVG color fill parity exists for triangle/voronoi/rectangles but palette controls still basic.


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
