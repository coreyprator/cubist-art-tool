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

---

*See also: [README.md](../README.md)*
