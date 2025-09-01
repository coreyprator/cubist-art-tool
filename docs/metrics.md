# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: docs/metrics.md
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:00+02:00
# === CUBIST STAMP END ===
# Metrics Format and Determinism

## Schema

Each run emits a `metrics.json` file with the following structure:

```json
{
  "totals": {
    "geometry_mode": "delaunay",
    "points": 200,
    "stages": 3,
    "seed": 123,
    "svg_shape_count": 150,
    "output_png": "your_input_image_00200pts_delaunay_cascade3_TIMESTAMP.png",
    "output_svg": "your_input_image_00200pts_delaunay_cascade3_TIMESTAMP.svg"
    // ...other fields may be present
  },
  "stages": [
    {
      "stage": 1,
      "geometry_mode": "delaunay",
      "points": 67,
      "svg_shape_count": 50,
      "seed": 123
    },
    {
      "stage": 2,
      "geometry_mode": "delaunay",
      "points": 134,
      "svg_shape_count": 100,
      "seed": 123
    },
    {
      "stage": 3,
      "geometry_mode": "delaunay",
      "points": 200,
      "svg_shape_count": 150,
      "seed": 123
    }
  ]
}
```

- **totals:** Summary of the run (geometry, points, stages, seed, shape counts, output file names).
- **stages:** List of per-stage metrics (for cascade runs), each with stage index, geometry, points, shape count, and seed.

## Normalization Rules

To ensure deterministic comparison, metrics are normalized as follows:

- **Basename normalization:**
  Output file paths (`output_png`, `output_svg`, etc.) are reduced to their base filename and any timestamp or run-specific digits are replaced with `TIMESTAMP` or `N`.
- **Timestamp scrubbing:**
  Any fields containing timestamps, durations, or elapsed times are removed.
- **Output directories:**
  Paths are replaced with `<OUTDIR>` or omitted.
- **Deep normalization:**
  All string fields are recursively scrubbed for temp directories, slashes, and timestamp patterns.

## Deterministic Fields

For runs with the same:
- `geometry_mode`
- `points`
- `stages`
- `seed`
- input image and mask

**The following fields must be identical:**
- `totals.geometry_mode`
- `totals.points`
- `totals.stages`
- `totals.seed`
- `totals.svg_shape_count`
- All per-stage fields except for output paths/timestamps

**Output file names** (e.g., `output_png`, `output_svg`) may differ in timestamp or run counter, but their normalized basenames should match.

## How to Diff Metrics Safely

- **Ignore:**
  - Any field containing timestamps, durations, or full output paths.
- **Compare:**
  - All semantic fields: geometry, points, stages, seed, shape counts.
  - Per-stage shape counts and points.
- **Recommended:**
  Use a JSON diff tool after normalization, or use the provided `stabilize_metrics` utility to preprocess both files before comparison.

## Example: Comparing Two Runs

1. Run both with the same seed and parameters.
2. Normalize both `metrics.json` files (see `metrics_utils.py`).
3. Compare the resulting JSONs; they should be identical except for non-semantic fields.

---

**Note:**
If you see differences in semantic fields for deterministic runs, this indicates a bug or non-determinism in the pipeline.


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:00+02:00
# === CUBIST FOOTER STAMP END ===
