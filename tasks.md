# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tasks.md
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:23:57+02:00
# === CUBIST STAMP END ===
# Cubist Art Generator — Roadmap & Tasks

## Release Notes Summary (v2.2)
- Fixed output directory handling (PNG/SVG outputs now consistent).
- Batch script supports multiple geometries, seeds, and cascade stages with consolidated logging.
- Determinism & metrics logging validated.
- SVG export implemented and working.
- Deterministic point sampling with `--seed`
- Geometry modes: delaunay, voronoi, rectangles
- Cascade fill (multi-stage refinement)
- PNG/SVG output with parity
- Metrics logging and normalization
- CLI argument validation and error handling

---

V2.3 + Tasks

## Phase 2: Presets, Config Loader, and UI/UX Front-End

- UI/UX front-end wrapper for easier user interaction
- Presets: save/load prior CLI configurations (geometry, cascade stages, seed, etc.) into JSON files
- UI provides dropdowns or selectors for launching with presets
- Marked as a requirement for the next release

## Phase 3: SVG Input Parsing & Timeline Scrubber

- SVG input parsing: user can input Illustrator-modified or simplified SVG files as a starting geometry, then re-run through the generator for iterative refinement
- Timeline scrubber UI: allows stepping through cascade fill frames interactively
- Automated playback export (animated GIF or MP4), with parameters for frames per second or frame duration per step

## Phase 4: Modular Plugin System (New Shape Logic)

- Modular architecture for adding new geometry modes independently
- Planned geometries for next release:
  - Hexagonal grids
  - Circle packing
  - Line hatch fills
  - Superellipse / squircle tessellation
  - L-systems or fractals
  - Image-derived contour primitives

---

## Historical Notes

- **Color LUT & Palette System:**
  Explored in early planning but deferred/eliminated in favor of using external color tools like Photoshop for advanced palette work.

- **AI-assisted Mask Generation:**
  Considered but rejected in favor of manual, human-controlled masks for higher artistic fidelity.


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:23:57+02:00
# === CUBIST FOOTER STAMP END ===
