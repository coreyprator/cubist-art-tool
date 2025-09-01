# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: main.py
# Version: v2.3.4
# Build: 2025-09-01T08:25:00
# Commit: n/a
# Stamped: 2025-09-01T08:36:04
# === CUBIST STAMP END ===
from svg_export import export_delaunay_svg
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--export_svg", action="store_true", help="Export results to SVG")
parser.add_argument(
    "--svg_filename", type=str, default="output.svg", help="SVG output filename"
)
args = parser.parse_args()

# After generating Delaunay triangles:
# points = ... (your input points)
# delaunay = scipy.spatial.Delaunay(points)
# triangles = [tuple(points[simplex]) for simplex in delaunay.simplices]

# Ensure name exists to satisfy Ruff even if earlier branches skip creation.
triangles = None

# Guard export_delaunay_svg with a check for triangles
if args.export_svg and triangles is not None:
    export_delaunay_svg(
        triangles, args.svg_filename, metadata={"creator": "Cubist Art Generator"}
    )
# === CUBIST FOOTER STAMP BEGIN ===
# End of file — v2.3.4 — stamped 2025-09-01T08:36:04
# === CUBIST FOOTER STAMP END ===
