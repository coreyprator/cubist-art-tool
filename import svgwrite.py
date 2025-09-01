# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: import svgwrite.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:44+02:00
# === CUBIST STAMP END ===

import svgwrite
from typing import List, Tuple


def export_delaunay_svg(
    triangles: List[
        Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]
    ],
    filename: str,
    metadata: dict = None,
):
    """
    Export Delaunay triangles to SVG.
    Args:
        triangles: List of triangles, each as 3 (x, y) tuples.
        filename: Output SVG file path.
        metadata: Optional dict for Illustrator-compatible metadata.
    """
    dwg = svgwrite.Drawing(filename, profile="full")

    # Add metadata (placeholder for Illustrator compatibility)
    if metadata:
        for key, value in metadata.items():
            dwg.add(svgwrite.base.Element("metadata", attrib={key: str(value)}))

    # Group for triangles
    triangle_group = dwg.add(dwg.g(id="delaunay-triangles"))

    for tri in triangles:
        triangle_group.add(
            dwg.polygon(points=tri, fill="none", stroke="black", stroke_width=1)
        )

    dwg.save()


def export_grouped_svg(groups: dict, filename: str, metadata: dict = None):
    """
    Export grouped/layered SVG output.
    Args:
        groups: Dict of {group_name: List of polygons}, each polygon as list of (x, y) tuples.
        filename: Output SVG file path.
        metadata: Optional dict for Illustrator-compatible metadata.
    """
    dwg = svgwrite.Drawing(filename, profile="full")

    # Add metadata (placeholder)
    if metadata:
        for key, value in metadata.items():
            dwg.add(svgwrite.base.Element("metadata", attrib={key: str(value)}))

    for group_name, polygons in groups.items():
        group = dwg.add(dwg.g(id=group_name))
        for poly in polygons:
            group.add(
                dwg.polygon(points=poly, fill="none", stroke="black", stroke_width=1)
            )
    dwg.save()


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:44+02:00
# === CUBIST FOOTER STAMP END ===
