# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: svg_export.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:23:58+02:00
# === CUBIST STAMP END ===

# ============================================================================
# Cubist Art Tool — SVG Export Utilities
# File: svg_export.py
# Version: v2.3-fixD
# Date: 2025-09-01
# Summary:
#   - write_svg: write a simple SVG from a list of shapes
#   - count_svg_shapes: count drawable elements in an SVG file
#
# Accepted shape inputs:
#   A) Dict-based (preferred):
#      {"type":"circle", "cx":.., "cy":.., "r":.., "stroke":..., "fill":..., "stroke_width":...}
#      {"type":"line", "x1":..,"y1":..,"x2":..,"y2":.., ...}
#      {"type":"rect","x":..,"y":..,"width":..,"height":.., "rx":?, "ry":?, ...}
#      {"type":"polygon","points":[(x,y),...], ...}
#      {"type":"polyline","points":[(x,y),...], ...}
#      {"type":"path","d":"M ... Z", ...}
#
#   B) Tuple triangle (compat with tests):
#      ((x1,y1), (x2,y2), (x3,y3))  -> written as <polygon>
#
# Numbers are formatted compactly (integers without decimals when possible).
# If use_mask=True, a minimal <mask> is emitted and shapes are wrapped with it,
# and a "MASK_PLACEHOLDER" comment is included for test compatibility.
# ============================================================================

from __future__ import annotations

from typing import Iterable, List, Tuple, Dict, Any, Union
from xml.etree import ElementTree as ET
import math
import os


# ------------------------- formatting helpers --------------------------------


def _fmt_num(v: Any) -> str:
    """Format numbers without trailing decimals when integral; else trimmed decimals."""
    try:
        if isinstance(v, bool):
            return "1" if v else "0"
        if isinstance(v, int):
            return str(v)
        f = float(v)
        if math.isfinite(f) and abs(f - round(f)) < 1e-9:
            return str(int(round(f)))
        s = f"{f:.3f}"
        return s.rstrip("0").rstrip(".")
    except Exception:
        return str(v)


def _fmt_color(c: Any) -> str:
    """
    Accepts:
      - CSS color string (e.g., "black", "#ff00aa", "none")
      - 3-tuple/list of ints 0..255 -> rgb(r,g,b)
    """
    if c is None:
        return "none"
    if isinstance(c, str):
        return c
    if isinstance(c, (tuple, list)) and len(c) == 3:
        try:
            r, g, b = [max(0, min(255, int(v))) for v in c]
            return f"rgb({_fmt_num(r)},{_fmt_num(g)},{_fmt_num(b)})"
        except Exception:
            return "none"
    return "none"


def _points_to_str(points: Iterable[Tuple[float, float]]) -> str:
    return " ".join(f"{_fmt_num(x)},{_fmt_num(y)}" for x, y in points)


# ----------------------------- public API ------------------------------------

ShapeInput = Union[
    Dict[str, Any], Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]
]


def write_svg(
    filename: str,
    shapes: List[ShapeInput],
    geometry: str = "unknown",
    width: int = 640,
    height: int = 480,
    background: Any = None,
    layer_name: str | None = None,
    metadata: Dict[str, Any] | None = None,
    stroke: Any = "black",
    fill_mode: Any = "none",
    use_mask: bool = False,
) -> None:
    """
    Write a valid SVG to `filename` from a list of shapes.

    - Supports dict-based shapes (circle/line/rect/polygon/polyline/path).
    - Also supports triangle tuples ((x1,y1),(x2,y2),(x3,y3)) as polygons.
    - If `use_mask` is True, inserts a minimal <mask> and wraps shapes in it.
    """
    lines: List[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_fmt_num(width)}" height="{_fmt_num(height)}">'
    )
    lines.append(f"  <!-- geometry:{geometry} -->")

    # Optional background
    if background not in (None, "none"):
        bg = _fmt_color(background)
        lines.append(
            f'  <rect x="0" y="0" width="{_fmt_num(width)}" height="{_fmt_num(height)}" fill="{bg}"/>'
        )

    # Optional layer group
    if layer_name:
        lines.append(f'  <g id="{layer_name}">')

    # Optional mask
    mask_id = None
    if use_mask:
        mask_id = "mask0"
        lines.append("  <defs>")
        lines.append("    <!-- MASK_PLACEHOLDER -->")
        # Solid white rect mask covering entire canvas (simple placeholder)
        lines.append(
            f'    <mask id="{mask_id}"><rect x="0" y="0" width="{_fmt_num(width)}" height="{_fmt_num(height)}" fill="white"/></mask>'
        )
        lines.append("  </defs>")
        lines.append(f'  <g mask="url(#{mask_id})">')

    default_stroke = _fmt_color(stroke)
    default_fill = _fmt_color(fill_mode)
    default_sw = 1

    def emit_polygon_from_points(
        pts: Iterable[Tuple[float, float]], st: str, sw: Any, fl: str
    ) -> None:
        pts_str = _points_to_str(pts)
        lines.append(
            f'  <polygon points="{pts_str}" stroke="{st}" stroke-width="{_fmt_num(sw)}" fill="{fl}"/>'
        )

    # Render shapes
    for s in shapes or []:
        # Triangle tuple form => polygon
        if (
            isinstance(s, (tuple, list))
            and len(s) == 3
            and all(isinstance(p, (tuple, list)) and len(p) == 2 for p in s)
        ):
            emit_polygon_from_points(s, default_stroke, default_sw, default_fill)
            continue

        if not isinstance(s, dict):
            continue

        t = str(s.get("type", "")).lower()

        # Normalize style attrs
        sw = s.get("stroke_width", default_sw)
        st = _fmt_color(s.get("stroke", default_stroke))
        fl = _fmt_color(s.get("fill", default_fill))

        if t == "circle":
            cx = s.get("cx", 0)
            cy = s.get("cy", 0)
            r = max(0.0, float(s.get("r", 0)))
            lines.append(
                f'  <circle cx="{_fmt_num(cx)}" cy="{_fmt_num(cy)}" r="{_fmt_num(r)}" stroke="{st}" stroke-width="{_fmt_num(sw)}" fill="{fl}"/>'
            )

        elif t == "line":
            x1 = s.get("x1", 0)
            y1 = s.get("y1", 0)
            x2 = s.get("x2", 0)
            y2 = s.get("y2", 0)
            lines.append(
                f'  <line x1="{_fmt_num(x1)}" y1="{_fmt_num(y1)}" x2="{_fmt_num(x2)}" y2="{_fmt_num(y2)}" stroke="{st}" stroke-width="{_fmt_num(sw)}"/>'
            )

        elif t == "rect":
            x = s.get("x", 0)
            y = s.get("y", 0)
            w = s.get("width", 0)
            h = s.get("height", 0)
            rx = s.get("rx", None)
            ry = s.get("ry", None)
            if rx is None and ry is None:
                lines.append(
                    f'  <rect x="{_fmt_num(x)}" y="{_fmt_num(y)}" width="{_fmt_num(w)}" height="{_fmt_num(h)}" stroke="{st}" stroke-width="{_fmt_num(sw)}" fill="{_fmt_num_color_or(fl)}"/>'
                )
            else:
                rxv = 0 if rx is None else rx
                ryv = 0 if ry is None else ry
                lines.append(
                    f'  <rect x="{_fmt_num(x)}" y="{_fmt_num(y)}" width="{_fmt_num(w)}" height="{_fmt_num(h)}" rx="{_fmt_num(rxv)}" ry="{_fmt_num(ryv)}" stroke="{st}" stroke-width="{_fmt_num(sw)}" fill="{_fmt_num_color_or(fl)}"/>'
                )

        elif t in ("polygon", "polyline"):
            pts = s.get("points", [])
            if isinstance(pts, (list, tuple)) and pts:
                if t == "polygon":
                    emit_polygon_from_points(pts, st, sw, fl)
                else:
                    pts_str = _points_to_str(pts)
                    lines.append(
                        f'  <polyline points="{pts_str}" stroke="{st}" stroke-width="{_fmt_num(sw)}" fill="none"/>'
                    )

        elif t == "path":
            d = s.get("d", "")
            if isinstance(d, str) and d.strip():
                lines.append(
                    f'  <path d="{d}" stroke="{st}" stroke-width="{_fmt_num(sw)}" fill="{fl}"/>'
                )

        else:
            # unknown shape; ignore silently
            continue

    if use_mask:
        lines.append("  </g>")  # close masked group

    if layer_name:
        lines.append("  </g>")  # close layer group

    # Minimal metadata comment
    if metadata:
        try:
            lines.append(f"  <!-- metadata:{metadata} -->")
        except Exception:
            pass

    lines.append("</svg>")

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _fmt_num_color_or(val: str) -> str:
    """
    Ensure color strings like rgb(...) or 'none' pass through unchanged.
    (Helper kept separate to avoid calling _fmt_num on colors.)
    """
    return val


def count_svg_shapes(svg_path: str) -> int:
    """
    Count drawable shape elements in an SVG. We include:
      circle, line, rect, polygon, polyline, path, ellipse
    """
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except Exception:
        # Fallback: permissive substring count
        try:
            txt = open(svg_path, "r", encoding="utf-8", errors="ignore").read().lower()
            total = 0
            for tag in (
                "<circle",
                "<line",
                "<rect",
                "<polygon",
                "<polyline",
                "<path",
                "<ellipse",
            ):
                total += txt.count(tag)
            return total
        except Exception:
            return 0

    def local(tag: str) -> str:
        return tag.split("}", 1)[1] if "}" in tag else tag

    SHAPES = {"circle", "line", "rect", "polygon", "polyline", "path", "ellipse"}

    def walk(n) -> int:
        count = 1 if local(n.tag) in SHAPES else 0
        for c in list(n):
            count += walk(c)
        return count

    return walk(root)


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:23:58+02:00
# === CUBIST FOOTER STAMP END ===
