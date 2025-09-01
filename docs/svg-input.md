# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: docs/svg-input.md
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:46+02:00
# === CUBIST STAMP END ===
# SVG Input Support (`--input-svg`)

**Status:** v2.3 feature (in progress)

## Overview

Cubist Art Tool v2.3 adds support for using SVG files as input geometry via the `--input-svg` CLI flag. This enables workflows starting from vector editors (e.g., Illustrator, Inkscape) or hand-crafted SVGs.

## CLI Flags

- `--input-svg PATH`
  Use an SVG file as the input geometry (mutually exclusive with `--input` raster image).
- `--svg-simplify-tol FLOAT`
  Douglas-Peucker simplification tolerance (default: 0.0 = off). Higher values simplify curves and polygons.

## How It Works

- Parses SVG shapes (lines, polygons, paths) into internal polygons.
- Optionally simplifies geometry using the specified tolerance.
- Passes the result into the existing render pipeline.
- Geometry mode can be applied as a post-process, or use a new `svg` mode.

## Limitations

- Only basic SVG shapes (lines, polygons, paths) are supported.
- Curves are approximated as polygons.
- Strokes vs. fills: Only filled shapes are imported; strokes are ignored.
- Malformed SVGs may fail to parse.

## Examples

```powershell
python cubist_cli.py --input-svg "input\example.svg" --geometry svg --output output\svgtest --export-svg
python cubist_cli.py --input-svg "input\example.svg" --svg-simplify-tol 2.5 --geometry delaunay --output output\svgtest --export-svg
```

## Tests

- Minimal SVGs (triangle, square, star)
- Malformed SVGs (error handling)
- Simplification golden tests

---

*See also: [README.md](../README.md)*



# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:46+02:00
# === CUBIST FOOTER STAMP END ===
