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

def write_svg_compat(*, filename=None, shapes=None, geometry=None, layer_name=None, metadata=None,
                     stroke=None, fill_mode=None, use_mask=False, width=None, height=None, **kwargs):
    """
    Backwards compatible entrypoint used by older tests.
    Maps old keyword names to the current write_svg signature.
    """
    if filename is None:
        raise ValueError("filename is required")
    if shapes is None:
        shapes = []
    # Fallback width/height if not provided
    if width is None:
        width = 1024
    if height is None:
        height = 1024
    # Prepare stroke/palette options
    palette = None
    stroke_opts = {"color": stroke, "width": 1, "alpha": 1.0} if stroke else None
    return write_svg(
        svg_path=str(filename),
        shapes=shapes,
        width=width,
        height=height,
        geometry_mode=geometry or "delaunay",
        palette=palette,
        stroke=stroke_opts,
    )

# Keep old name alive for tests that import write_svg directly
# by providing a thin proxy that detects the call pattern:
_original_write_svg = write_svg

def write_svg(*args, **kwargs):
    if "filename" in kwargs or "geometry" in kwargs or "layer_name" in kwargs:
        return write_svg_compat(**kwargs)
    return _original_write_svg(*args, **kwargs)