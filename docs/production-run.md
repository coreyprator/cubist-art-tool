# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: docs/production-run.md
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:46+02:00
# === CUBIST STAMP END ===
# Production Batch Runs with Cubist Art Generator

## Overview

The `scripts/run_production.ps1` script automates batch runs of the cubist CLI across multiple geometries, cascade stages, and seeds. This enables robust testing, reproducibility, and large-scale art generation.

- **Scenarios:** All combinations of geometries × cascade stages × seeds.
- **Geometries:** `delaunay`, `voronoi`, `rectangles`
- **Cascade stages:** e.g., `1,3`
- **Seeds:** e.g., `123,456`

---

## Core Concepts

### Metrics

**What are metrics?**
Metrics are a structured summary ("flight recorder") of each run, capturing key statistics such as:
- Geometry type (e.g., delaunay, voronoi, rectangles)
- Number of points sampled
- Number of cascade stages
- Number of shapes rendered (for both PNG and SVG)
- Output file paths (PNG, SVG)
- Seed used for random sampling

**Why are metrics important?**
- They allow you to compare runs for reproducibility and benchmarking.
- They make it easy to validate that PNG and SVG outputs match.
- They provide a record for debugging and batch analysis.

### Determinism & Seeds

**Randomness in geometry:**
The tessellation and colorization algorithms use random sampling. Without a fixed seed, each run produces different results.

**Determinism:**
If you use the same input image, parameters, and seed, you will get identical outputs (PNG, SVG, metrics). This is crucial for reproducibility and scientific comparison.

**Two levels of seeds:**
- **Outer loop (`-Seeds` in `run_production.ps1`):**
  Controls the batch, allowing you to run the same scenario with different seeds for variability studies.
- **Inner seed (`--seed` in `cubist_cli.py`):**
  The actual seed used by the geometry algorithm for that run.

This design lets you explore both reproducibility (same seed) and variability (different seeds) in a controlled way.

### Cascade Stages

**What is a cascade stage?**
A cascade stage is a refinement pass in the tessellation process. More stages mean more detail and layering.

- **Stage 1:** One pass, fast, produces a coarse result.
- **Stage 3:** Three passes, adds detail and visual complexity.

**Adjustable:**
You can set the number of stages with `-CascadeStages` in the batch script or `--cascade-stages` in the CLI. Higher values trade performance for detail.

### SVG Limit

**Why limit SVG shapes?**
SVG files can become very large and slow to open in vector editors if they contain thousands of shapes.

**SvgLimit parameter:**
Use `--svg-limit` (CLI) or `-SvgLimit` (batch) to cap the number of shapes written to the SVG.

**Example:**
`--svg-limit 150` exports only the first 150 polygons, keeping the SVG manageable for tools like Illustrator.

---

## Parameters

| Parameter         | Description                                                      | Example                          |
|-------------------|------------------------------------------------------------------|----------------------------------|
| `-Image`          | Path to input image                                              | `-Image "input\your_input_image.jpg"` |
| `-Points`         | Number of points to sample                                       | `-Points 200`                    |
| `-Geometries`     | Comma-separated list of geometries                               | `-Geometries "delaunay,voronoi,rectangles"` |
| `-CascadeStages`  | Comma-separated list of cascade stage counts                     | `-CascadeStages "1,3"`           |
| `-Seeds`          | Comma-separated list of seeds                                    | `-Seeds "123,456"`               |
| `-SvgLimit`       | Max number of shapes in SVG (optional)                           | `-SvgLimit 150`                  |
| `-TimeoutSeconds` | Per-run timeout in seconds (optional)                            | `-TimeoutSeconds 120`            |
| `-ExportSvg`      | Include to export SVGs                                           | `-ExportSvg`                     |
| `-VerboseLog`     | More logging                                                     | `-VerboseLog`                    |
| `-DryRun`         | Preview commands only, do not execute                            | `-DryRun`                        |

## Sample Invocation

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_production.ps1 `
  -Image "input\your_input_image.jpg" `
  -Points 200 `
  -Geometries "delaunay,voronoi,rectangles" `
  -CascadeStages "1,3" `
  -Seeds "123,456" `
  -SvgLimit 150 `
  -TimeoutSeconds 120 `
  -ExportSvg `
  -VerboseLog
```

## Output Folder Structure

- All outputs are placed in a timestamped root:
  `output\prod_<YYYYMMDD_HHMMSS>\`
- Each run gets its own subdirectory:
  `output\prod_<timestamp>\<geometry>_<scenario>`
- Inside each run directory:
  - PNG and SVG outputs
  - `metrics.json` (normalized, deterministic)
  - `run.log` (stdout)
  - `run_error.log` (stderr, if any)

- A consolidated error log for the batch:
  `output\prod_<timestamp>\run_errors.log`

## Logs and Error Files

- **Per-run logs:**
  - `run.log` — standard output from the CLI
  - `run_error.log` — standard error (exceptions, tracebacks)
- **Consolidated errors:**
  - `run_errors.log` in the batch root summarizes all failures for quick review.

## Tips for Large Runs

- **Disk usage:**
  Large batches can generate many images and logs. Monitor free space.
- **Cleaning outputs:**
  Use `scripts\clean_outputs.ps1` to remove old output folders:
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts\clean_outputs.ps1 -Root output -DryRun
  ```
- **Avoiding lockups:**
  Use `-TimeoutSeconds` to prevent stuck runs.
- **Dry run:**
  Use `-DryRun` to preview all commands before launching a big batch.

## Comparing Metrics Across Runs

- **Deterministic runs:**
  Runs with the same seed, geometry, and points will produce identical `metrics.json` and SVG outputs.
- **Different seeds:**
  Changing the seed will change the sampled points and thus the output and metrics.
- **Validation:**
  Compare `metrics.json` files to ensure reproducibility or to verify differences between parameter sets.

---

## Release Note Context

- **Output directory handling is now robust:**
  PNG and SVG files are reliably written to the expected run subdirectories.
- **Production script improvements:**
  Batch runs across geometries, seeds, and cascade stages are now supported, with consolidated error handling and deterministic metrics for easy comparison.



# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:46+02:00
# === CUBIST FOOTER STAMP END ===
