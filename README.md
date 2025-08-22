# Cubist Art Generator v2.3

[![Tested: delaunay / voronoi / rectangles (regular & cascade)](https://img.shields.io/badge/geometry-delaunay%2Fvoronoi%2Frectangles-blue)](#)

## 1. Installation

**Recommended:** Windows + PowerShell

- Install Python 3.13 (or 3.11+) and ensure it's on your PATH.
- Create a virtual environment:
  ```
  python -m venv .venv
  .\.venv\Scripts\activate
  ```
- Install dependencies:
  ```
  pip install -r requirements.txt
  ```
- *(Optional)* Enable pre-commit hooks and code style checks:
  ```
  pre-commit install
  ruff check .
  ```

## 2. Quick Start

**Hello World: Generate PNG + SVG with metrics**

```powershell
.\.venv\Scripts\activate
python cubist_cli.py ^
  --input "input\your_input_image.jpg" ^
  --output "output\quick_delaunay" ^
  --points 200 ^
  --geometry delaunay ^
  --cascade-stages 1 ^
  --seed 123 ^
  --export-svg ^
  --svg-limit 150 ^
  --timeout-seconds 120 ^
  --metrics-json "output\quick_delaunay\metrics.json" ^
  --verbose
```

- `--output` is a **directory**. PNG and SVG will be written inside it.
- Metrics and logs will also be placed in the output directory.

## 3. Production Batch

**Automated batch runs across geometries, cascades, and seeds:**

Use the provided PowerShell script:

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

**Parameters:**
- `-Image`         : Input image path
- `-Points`        : Number of points to sample
- `-Geometries`    : Comma-separated list (e.g. `"delaunay,voronoi,rectangles"`)
- `-CascadeStages` : Comma-separated list (e.g. `"1,3"`)
- `-Seeds`         : Comma-separated list (e.g. `"123,456"`)
- `-SvgLimit`      : Max SVG shapes (optional)
- `-TimeoutSeconds`: Per-run timeout (optional)
- `-ExportSvg`     : Include to export SVGs
- `-VerboseLog`    : More logging
- `-DryRun`        : Preview commands only

**Outputs:**
- Results are in `output\prod_<timestamp>\...`
- Each run has its own subdirectory with PNG, SVG, metrics, and logs.
- Consolidated errors: `output\prod_<timestamp>\run_errors.log`

## 4. Metrics & Determinism

- Every run emits a `metrics.json` with shape counts, geometry, seed, and other info.
- Metrics are normalized (paths/timestamps scrubbed) for deterministic comparison.
- **Seeded runs with the same parameters will produce identical metrics and SVGs.**
- Use metrics to validate PNG/SVG parity and reproducibility.

## 5. SVG Input (NEW in v2.3)

- Use `--input-svg PATH` to use an SVG file as input geometry (instead of a raster image).
- Optional: `--svg-simplify-tol FLOAT` to simplify imported SVG shapes.
- See [docs/svg-input.md](docs/svg-input.md) for details and limitations.

## 6. Troubleshooting

- **No PNG output found:**
  Make sure `--output` is a directory, not a filename. This is now handled automatically.
- **Missing packages:**
  Run `pip install -r requirements.txt` in your activated `.venv`.
- **Clean old outputs:**
  ```
  powershell -ExecutionPolicy Bypass -File scripts\clean_outputs.ps1 -Root output -DryRun
  ```
- **PowerShell execution policy:**
  If you get script execution errors, add `-ExecutionPolicy Bypass` to your PowerShell command.

---

**Tested geometries in v2.3:**
- delaunay (regular & cascade)
- voronoi (regular & cascade)
- rectangles (regular & cascade)
- svg (input SVG mode, new)
