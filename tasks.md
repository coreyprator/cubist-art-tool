# Cubist Art Generator – V2 Tasks

This file tracks the implementation plan for version 2 of the app.

## 🧱 Phase 1: Geometry Engine Upgrade
- [x] Refactor core logic to support multiple geometry modes
- [x] Implement Voronoi fill mode
- [x] Implement rectangle fill mode
- [x] Add geometry_mode field to config
- [x] Output files include geometry type in filename
- [x] Add CascadeFill toggle for all geometry modes
- [x] Create comprehensive CLI testing script
- [x] **ENHANCED**: Implement spatial optimization for cascade fill
- [x] **ENHANCED**: Add adjacency-based placement for better space utilization
- [x] **ENHANCED**: Implement distance transform and priority mapping
- [x] **ENHANCED**: Add rotational variety and organic shape generation

## 🎨 Phase 2: Color LUT & Palette System
- [ ] Load external LUT file (e.g., .cube, JSON)
- [ ] Apply LUT to triangle fill
- [ ] Add debug overlays for LUT effect
- [ ] Enable palette-constrained mode

## 🧪 Phase 3: Stepwise Fill Preview (CLI)
- [x] Implement incremental shape-fill preview logic (CascadeFill)
- [x] Export each step as a separate PNG (batch mode)
- [x] Allow step size setting in config (save_step_frames parameter)
- [x] Create CLI interface for testing all modes

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
