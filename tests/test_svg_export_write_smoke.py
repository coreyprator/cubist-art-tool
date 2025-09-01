# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tests/test_svg_export_write_smoke.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:00+02:00
# === CUBIST STAMP END ===

# ======================================================================
# File: tests/test_svg_export_write_smoke.py
# Stamp: 2025-08-24T22:00:00Z
# (Auto-added header for paste verification)
# ======================================================================

import tempfile
import os
from svg_export import write_svg

def test_svg_export_write_smoke():
    shapes = [
        {"type": "rect", "x": 10, "y": 20, "width": 30, "height": 40, "fill": (12, 34, 56)},
        {"type": "polygon", "points": [(0, 0), (10, 0), (10, 10)], "fill": "#112233"},
        {"type": "circle", "cx": 50, "cy": 50, "r": 12, "fill": "none", "stroke": (200, 100, 0), "stroke_width": 2},
    ]
    with tempfile.TemporaryDirectory() as td:
        svg_path = os.path.join(td, "test.svg")
        write_svg(svg_path, shapes, geometry="smoke", width=100, height=100)
        assert os.path.exists(svg_path)
        with open(svg_path, "r", encoding="utf-8") as f:
            svg = f.read()
        assert "<rect" in svg
        assert "<polygon" in svg
        assert "<circle" in svg
        assert 'fill="rgb(12,34,56)"' in svg or 'fill="#112233"' in svg
        assert 'fill="none"' in svg  # circle intentionally uses fill="none"

# ======================================================================
# End of File: tests/test_svg_export_write_smoke.py  (2025-08-24T22:00:00Z)
# ======================================================================



# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:00+02:00
# === CUBIST FOOTER STAMP END ===
