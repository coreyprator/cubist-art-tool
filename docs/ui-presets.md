# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: docs/ui-presets.md
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:00+02:00
# === CUBIST STAMP END ===
# UI/UX Wrapper & Presets (v2.3+)

**Status:** Planned for next release

## Overview

A minimal local UI wrapper (Python + tkinter or PySimpleGUI) will allow users to configure and launch the CLI visually.

## Features

- Load/Save presets (JSON) under `/presets`
  - Presets include geometry, points, cascade stages, SVG limit, seed, export options, etc.
- "Run" button launches the CLI with chosen parameters and shows a live log tail.
- "Open output folder" button on completion.
- CLI fallback: `--preset NAME` and `--save-preset NAME` flags.

## Example Preset JSON

```json
{
  "geometry": "delaunay",
  "points": 200,
  "cascade_stages": 3,
  "svg_limit": 150,
  "seed": 123,
  "export_svg": true
}
```

## CLI Usage

```powershell
python cubist_cli.py --preset "my_favorite" --output output\from_preset --export-svg
python cubist_cli.py --save-preset "new_preset" --geometry voronoi --points 100 --output output\save
```

## Tests

- Preset round-trip (load/save) unit tests
- Smoke test: launch CLI with a preset

---

*See also: [README.md](../README.md)*


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:00+02:00
# === CUBIST FOOTER STAMP END ===
