# Cubist Art Generator – V2 Tasks

This file tracks the implementation plan for version 2 of the app.

## 🧱 Phase 1: Geometry Engine Upgrade
- [ ] Refactor core logic to support multiple geometry modes
- [ ] Implement Voronoi fill mode
- [ ] Implement rectangle fill mode
- [ ] Add geometry_mode field to config
- [ ] Output files include geometry type in filename

## 🎨 Phase 2: Color LUT & Palette System
- [ ] Load external LUT file (e.g., .cube, JSON)
- [ ] Apply LUT to triangle fill
- [ ] Add debug overlays for LUT effect
- [ ] Enable palette-constrained mode

## 🧪 Phase 3: Stepwise Fill Preview (CLI)
- [ ] Implement incremental shape-fill preview logic
- [ ] Export each step as a separate PNG (batch mode)
- [ ] Allow step size setting in config

## 🧰 Phase 4: Presets & Config Loader
- [ ] Load/save presets (geometry + color settings)
- [ ] Add preset manager CLI options
- [ ] Store presets as JSON files in /presets/

## 🖼 Phase 5: SVG Export
- [ ] Basic vector export for Delaunay results
- [ ] Grouped/layered SVG output
- [ ] Illustrator-compatible metadata

## 🧠 Phase 6+: Future
- [ ] AI-assisted mask generation (external tool hook)
- [ ] SVG input parsing (optional)
- [ ] Timeline scrubber UI
- [ ] Modular plugin system for new shape logic
