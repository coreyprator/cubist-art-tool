# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: docs/SVG_GUIDE.md
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:46+02:00
# === CUBIST STAMP END ===
SVG Export Guide
================

This guide explains the SVG export functionality, including compatibility with Adobe Illustrator, layer and mask handling, color and metadata support, and usage tips.

## Illustrator Compatibility
- SVGs exported are compatible with Adobe Illustrator.
- Metadata is embedded for easier asset management.

## Layers
- Each geometry type (Delaunay, Voronoi, Rectangles) can be exported to a separate SVG group (`<g>`), optionally named via `layer_name`.

## Mask Handling
- If `use_mask` is enabled, a mask placeholder is included in the SVG.
- Actual mask logic should be implemented as needed.

## Color Handling
- Shapes can be exported with stroke and fill options.
- `fill_mode` controls whether shapes are filled or transparent.

## Metadata
- Metadata such as geometry type, cascade, and points can be embedded in the SVG `<metadata>` tag.

## Tips
- For best results in Illustrator, use the exported SVG as a base layer.
- Edit layer/group names in Illustrator for organization.
- Use the mask placeholder as a guide for advanced masking.



# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:46+02:00
# === CUBIST FOOTER STAMP END ===
