# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: README.md
# Version: v2.3# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:43+02:00
# === CUBIST STAMP END ===
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

## How to truly clear the entire terminal output (not just visible pane)

You're right! <kbd>Ctrl</kbd>+<kbd>L</kbd> only clears the visible screen, not the scrollback buffer.

**For a true "cls" equivalent in VS Code:**

- **Best option:** <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> → type "Terminal: Clear" → select **"Terminal: Clear"**
  - This completely clears all terminal output and scrollback buffer
  - Same as typing `cls` in PowerShell

**Alternative methods:**

- **PowerShell:** Type `Clear-Host` (same as `cls`)
- **Command Palette shortcut:** You can assign a custom keybinding:
  1. <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> → "Preferences: Open Keyboard Shortcuts"
  2. Search for "Terminal: Clear"
  3. Click the + to add a keybinding (e.g., <kbd>Ctrl</kbd>+<kbd>K</kbd>, <kbd>Ctrl</kbd>+<kbd>C</kbd>)

**Summary:**
- <kbd>Ctrl</kbd>+<kbd>L</kbd> = Clear visible screen only (scrollback remains)
- Command Palette → "Terminal: Clear" = True `cls` equivalent (clears everything)
- Type `cls` or `Clear-Host` = Also clears everything

**Tip:** The Command Palette method works in any terminal (PowerShell, Command Prompt, Git Bash, etc.) within VS Code.

---

**Tested geometries in v2.3:**
- delaunay (regular & cascade)
- voronoi (regular & cascade)
- rectangles (regular & cascade)
- svg (input SVG mode, new)

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:43+02:00
(input SVG mode, new)


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:23:57+02:00
 svg (input SVG mode, new)

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:27+02:00
# === CUBIST FOOTER STAMP END ===
- delaunay (regular & cascade)
- voronoi (regular & cascade)
- rectangles (regular & cascade)
- svg (input SVG mode, new)

# PowerShell equivalent commands (wc is a Unix/Linux command, not available in PowerShell)

# Count files in git (PowerShell equivalent)
git ls-files | Measure-Object -Line | Select-Object -ExpandProperty Lines

# Or shorter version:
(git ls-files).Count

# Other useful PowerShell equivalents:
# Count lines in a file:
Get-Content filename.txt | Measure-Object -Line

# Count files in current directory:
(Get-ChildItem).Count

# Count Python files:
(Get-ChildItem -Filter "*.py" -Recurse).Count
(Get-ChildItem).Count

# Count Python files:
(Get-ChildItem -Filter "*.py" -Recurse).Count
