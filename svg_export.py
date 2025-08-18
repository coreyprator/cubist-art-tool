"""
Minimal SVG export helpers for Cubist Art Generator.
No external deps. Writes valid SVG with metadata and optional placeholder layer.
"""

from datetime import datetime
from typing import Optional, Iterable, Dict, Any
from pathlib import Path
import os
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, ElementTree

def count_svg_shapes(svg_path: str,
                     tags: tuple[str, ...] = ("polygon", "path", "rect")) -> int:
    """
    Count visible vector shapes in an SVG by tag.
    Defaults to polygon/path/rect which cover delaunay/voronoi/rectangles.
    Handles XML namespaces gracefully.
    """
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except Exception:
        return 0

    def local(tag: str) -> str:
        return tag.split('}', 1)[-1] if '}' in tag else tag

    want = set(tags)
    cnt = 0
    for el in root.iter():
        if local(el.tag) in want:
            cnt += 1
    return cnt

def _rgb_tuple_to_css(rgb):
    r, g, b = (int(max(0, min(255, c))) for c in rgb)
    return f"rgb({r},{g},{b})"

def _to_css(val):
    # Accept (r, g, b) tuples/lists or strings like "#aabbcc"/"rgb(...)"
    if isinstance(val, (tuple, list)) and len(val) == 3:
        return _rgb_tuple_to_css(val)
    return str(val) if val is not None else "#000000"

def write_svg(
    svg_path: str,
    shapes: list,
    width: int,
    height: int,
    geometry_mode: str,
    palette=None,
    stroke=None,
    stroke_width: float = 0.0,
    background=None,
    max_shapes: int | None = None
) -> None:
    """
    Write SVG from provided shapes (no resampling, no preview limit unless max_shapes is set).
    """
    if max_shapes is not None:
        shapes = shapes[:max_shapes]
    print(f"SVG write: shapes={len(shapes)}, geometry={geometry_mode}, size={width}x{height}")

    out_path = str(svg_path)
    Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)

    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "version": "1.1",
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
        },
    )

    # Background (white so preview isn't transparent)
    ET.SubElement(svg, "rect", {"x": "0", "y": "0", "width": "100%", "height": "100%", "fill": "#ffffff"})

    g = ET.SubElement(svg, "g", {"id": geometry_mode})

    for shp in shapes:
        t = shp.get("type")
        if t is None:
            if "points" in shp:
                t = "polygon"
            elif all(k in shp for k in ("x", "y", "w", "h")):
                t = "rect"
            elif "d" in shp:
                t = "path"
        if t == "rect":
            ET.SubElement(
                g, "rect",
                {
                    "x": str(shp["x"]), "y": str(shp["y"]),
                    "width": str(shp["w"]), "height": str(shp["h"]),
                    "fill": _to_css(shp.get("fill", "#000000")),
                    "stroke": _to_css(shp.get("stroke", "#000000")),
                    "stroke-width": str(shp.get("stroke_width", 1)),
                },
            )
        elif t == "polygon":
            pts = " ".join(f"{int(x)},{int(y)}" for x, y in shp["points"])
            ET.SubElement(
                g, "polygon",
                {
                    "points": pts,
                    "fill": _to_css(shp.get("fill", "#000000")),
                    "stroke": _to_css(shp.get("stroke", "#000000")),
                    "stroke-width": str(shp.get("stroke_width", 1)),
                },
            )
        elif t == "path":
            ET.SubElement(
                g, "path",
                {
                    "d": shp["d"],
                    "fill": _to_css(shp.get("fill", "#000000")),
                    "stroke": _to_css(shp.get("stroke", "#000000")),
                    "stroke-width": str(shp.get("stroke_width", 1)),
                },
            )

    ElementTree(svg).write(svg_path, encoding="utf-8", xml_declaration=True)
    return out_path