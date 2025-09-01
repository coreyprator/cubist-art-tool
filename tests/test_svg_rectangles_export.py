# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tests/test_svg_rectangles_export.py
# Version: v2.3.4
# Build: 2025-09-01T08:25:00
# Commit: n/a
# Stamped: 2025-09-01T08:36:05
# === CUBIST STAMP END ===
# ======================================================================
# File: tests/test_svg_rectangles_export.py
# Stamp: 2025-08-22T18:10:00Z
# (Auto-added header for paste verification)
# ======================================================================

import tempfile
import os
from svg_export import write_svg

def test_svg_rectangles_export_writes_rect_with_fill():
    shapes = [
        {"type": "rect", "x": 10, "y": 20, "width": 30, "height": 40, "fill": (12, 34, 56)}
    ]
    with tempfile.TemporaryDirectory() as td:
        svg_path = os.path.join(td, "test_rect.svg")
        write_svg(svg_path, shapes, width=100, height=100)
        with open(svg_path, "r", encoding="utf-8") as f:
            svg = f.read()
        assert "<rect" in svg
        assert 'fill="' in svg
        assert "rgb(12,34,56)" in svg
        assert "width=\"30\"" in svg
        assert "height=\"40\"" in svg
        assert "x=\"10\"" in svg
        assert "y=\"20\"" in svg

# ======================================================================
# End of File: tests/test_svg_rectangles_export.py  (2025-08-22T18:10:00Z)
# ======================================================================
# === CUBIST FOOTER STAMP BEGIN ===
# End of file — v2.3.4 — stamped 2025-09-01T08:36:05
# === CUBIST FOOTER STAMP END ===
