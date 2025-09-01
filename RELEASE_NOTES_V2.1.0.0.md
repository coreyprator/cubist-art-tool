# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: RELEASE_NOTES_V2.1.0.0.md
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:29+02:00
# === CUBIST STAMP END ===
# v2.1.0 — PNG/SVG lockstep + validation 🥳

## Highlights
- **True parity**: SVG now renders from the **same sampled points** as PNG for all geometries.
- **Determinism**: `--seed` gives repeatable results across runs and formats.
- **Validation**: The CLI now prints a `METRICS:` line; the test harness can parse and verify that
  **SVG shape count == raster count**. No more “mystery 20 points” SVGs.
- **Usability**: Archive-only invocations exit cleanly. Errors are explicit and quiet-mode friendly.

## What changed under the hood
- Unified point sampling (adds corners for certain modes) → single source of truth feeds both raster and vector.
- `svg_export` consumes the exact geometry emitted to the rasterizer.
- Added `METRICS:` emission to `cubist_cli.py` so `test_cli.py` can assert parity without reading files.

## How to reproduce the triple test
```powershell
python test_cli.py `
  --input input/your_input_image.jpg `
  --output output `
  --triple-test `
  --points 100 `
  --export-svg `
  --seed 42 `
  --timeout-seconds 120

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:29+02:00
# === CUBIST FOOTER STAMP END ===
