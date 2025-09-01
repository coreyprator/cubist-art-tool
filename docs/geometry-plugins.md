# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: docs/geometry-plugins.md
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:00+02:00
# === CUBIST STAMP END ===
# Modular Geometry Plug-in System

**Status:** v2.3 feature (planned)

## Overview

Geometry modes are now modular plug-ins, making it easy to add new tessellation or fill strategies.

## How It Works

- Each geometry is registered via `register_geometry("name", handler)`.
- Built-in geometries: delaunay, voronoi, rectangles (migrated to plugins/geometry_*.py).
- New geometries can be added as separate Python files in `plugins/`.

## Adding a New Geometry

1. Create a new file: `plugins/geometry_hex.py`
2. Implement a function: `def geometry_hex(...):`
3. Register it in the plugin file:
   ```python
   from geometry_registry import register_geometry
   register_geometry("hex", geometry_hex)
   ```
4. The CLI will automatically list available geometries.

## Planned Geometries

- squares
- hex
- strokes
- pointillism
- quads
- curvy (path-based)
- hexagonal grids
- circle packing
- line hatch fills
- superellipse / squircle tessellation
- L-systems or fractals
- image-derived contour primitives

## CLI Usage

```powershell
python cubist_cli.py --geometry hex --input input\your_input_image.jpg --output output\hex --points 100
```

## Tests

- Registry discovery test
- Minimal plugin unit test

## Current Limitations (Initial v2.3)

- Plugins can be discovered and selected by name using `--geometry <plugin_name>`.
- In this initial v2.3 release, plugin geometry is **not executed**. If a plugin is selected, the CLI prints an audit notice and falls back to the built-in `rectangles` mode to ensure production stability.
- Execution of plugin geometry will be enabled in a follow-up PR after additional parity and safety checks.

## Determinism in the Cubist Art Tool

- **Definition:** Given the same image, parameters (e.g., points, geometry), and seed, the tool must always produce identical geometry and metrics, regardless of time, machine, or OS.
- **Why we care:** Reproducible artwork (a saved seed regenerates the same visual), stable tests and metrics (no flaky CI), cross-platform consistency, and plugin discipline.
- **Python/NumPy practice:** Use seeded RNGs (`np.random.default_rng(seed)` or `random.seed(seed)`), avoid time-based entropy or unseeded random calls.
- **Plugin checklist:**
  - Accept and honor a `seed` parameter.
  - Avoid system clock or OS entropy.
  - Ensure outputs are pure functions of `(image_shape, total_points, seed)`.
  - Sanity test: same seed → identical output.

By following these guidelines, plugin authors and contributors help maintain the Cubist Art Tool’s promise of reproducibility and reliability for all users.

## Example: scatter_circles

A deterministic plugin that scatters circles across the image using a stratified jitter grid. Each circle is placed in a grid cell with random jitter, and the color is sampled at the center. The output is a list of (cx, cy, r) tuples.

```python
# geometry_plugins/scatter_circles.py

import math
import random

def geometry_fn(image_shape, total_points: int, seed: int):
    # ...see plugin source for full details...
    # Returns list of (cx, cy, r) ints.
    pass

def register(register_fn):
    register_fn("scatter_circles", geometry_fn)
```

---

*See also: [README.md](../README.md)*


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:00+02:00
# === CUBIST FOOTER STAMP END ===
