# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: docs/production-ui.md
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:00+02:00
# === CUBIST STAMP END ===
# Cubist Art Tool — Production Runner UI

The Production Runner UI (`tools/prod_ui.py`) provides a simple graphical interface to run the CLI for multiple geometries and plugins, manage output folders, and save/load run configurations.

## Features

- **Checkboxes** for built-in geometries (delaunay, voronoi, rectangles) and discovered plugins.
- **Input controls** for image path, points, seed, cascade stages, export SVG, and plugin exec toggle.
- **Output folder**: Each run creates a timestamped folder under `output/production/YYYYmmdd-HHMMss/`.
- **Archive/clean options**: Clean previous production outputs before run (dangerous; confirmation required).
- **Config load/save**: Save and load all UI settings to/from `configs/prod_ui.json`.
- **Log area**: Shows CLI output and a file audit for each geometry.
- **Open Output Folder**: Opens the timestamped output folder in Explorer/Finder.

## How to Use

1. **Start the UI**:
   ```
   python tools/prod_ui.py
   ```

2. **Select geometries and plugins**:
   - Check the built-in geometries and/or plugins you want to run.
   - For plugins, you may need to enable "Enable plugin exec" for actual plugin execution.

3. **Set input files and parameters**:
   - Browse for your input image.
   - Set points, seed, cascade stages, and other options.

4. **Choose output and cleaning options**:
   - The output folder is shown and will be timestamped.
   - Optionally clean previous production outputs (dangerous).

5. **Run**:
   - Click "Run Selected" to start.
   - The log area will show CLI output and a file list for each geometry.

6. **Save/Load Config**:
   - Save your current settings to `configs/prod_ui.json` for future use.
   - Load them back at any time.

7. **Open Output Folder**:
   - After a run, click "Open Output Folder" to view results.

## Advanced: SVG Passthrough (Dev Only)

- SVG passthrough is hidden by default.
- To enable, press **Ctrl+Shift+S** to reveal the dev panel.
- You can then select an input SVG and enable SVG passthrough for internal testing.
- This is not intended for normal production runs.

## Example Screenshot

*(screenshot placeholder)*

![Production Runner UI Screenshot](production-ui-screenshot.png)

## Notes

- The UI generates PNG + optional SVG export for each selected geometry.
- Plugin execution is only enabled if "Enable plugin exec" is checked.
- Output folders are never overwritten unless you explicitly clean them.

---


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:00+02:00
# === CUBIST FOOTER STAMP END ===
