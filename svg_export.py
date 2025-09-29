#!/usr/bin/env python3
"""
SVG Export Fallback System
Provides export_svg function as last resort when plugins don't have exporters.
"""


def _to_rgb_string(val):
    """Normalize color spec to CSS rgb(r,g,b) or pass-through strings."""
    if val is None:
        return None
    # tuple/list of numbers
    if isinstance(val, (list, tuple)) and len(val) >= 3:
        try:
            r, g, b = int(val[0]), int(val[1]), int(val[2])
            return f"rgb({r},{g},{b})"
        except Exception:
            return str(val)
    # string representations like "(200, 204, 239)" → rgb
    if isinstance(val, str):
        s = val.strip()
        # match "(r, g, b)" numeric tuple
        if s.startswith("(") and s.endswith(")"):
            parts = s[1:-1].split(",")
            if len(parts) >= 3:
                try:
                    r, g, b = [int(float(p.strip())) for p in parts[:3]]
                    return f"rgb({r},{g},{b})"
                except Exception:
                    pass
        # already rgb(...) or hex or named color: return as-is
        return s
    # fallback: cast to str
    return str(val)


def export_svg(shapes, width=800, height=600, background="white"):
    """
    Export shapes to SVG format as fallback when plugin exporters fail.

    Args:
        shapes: List of shape dictionaries with 'type' key and shape-specific keys
        width, height: Canvas dimensions
        background: Background color

    Returns:
        str: SVG content as string
    """

    svg_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="100%" height="100%" fill="{background}"/>',
    ]
    shape_count = 0
    for shape in shapes:
        if not isinstance(shape, dict):
            continue
        shape_count += 1
        shape_type = shape.get("type", "").lower()
        # Normalize fill/stroke up front for consistent usage
        fill_raw = shape.get("fill", None)
        stroke_raw = shape.get("stroke", None)
        fill_color = _to_rgb_string(fill_raw) or f"hsl({(shape_count*137)%360},70%,50%)"
        stroke_color = _to_rgb_string(stroke_raw) or "none"
        stroke_width = shape.get("stroke-width", shape.get("stroke_width", 0.5))
        # circle handling
        if shape_type == "circle":
            cx = shape.get("cx", 0)
            cy = shape.get("cy", 0)
            r = shape.get("r", 1)
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_width}"/>'
            )
            continue
        points = shape.get("points", [])
        if not points:
            continue
        # Polygons / triangles
        if shape_type == "triangle" and len(points) >= 3:
            pts = points[:3]
            path_data = f"M {pts[0][0]},{pts[0][1]} L {pts[1][0]},{pts[1][1]} L {pts[2][0]},{pts[2][1]} Z"
            svg_parts.append(
                f'<path d="{path_data}" fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_width}" opacity="0.7"/>'
            )
            continue
        # generic polygon fallback
        points_str = " ".join(f"{int(p[0])},{int(p[1])}" for p in points)
        svg_parts.append(
            f'<polygon points="{points_str}" fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_width}" opacity="0.7"/>'
        )

    svg_parts.append("</svg>")

    print(f"SVG export fallback: exported {shape_count} shapes")
    return "\n".join(svg_parts)


def save_svg(shapes, filepath, width=800, height=600, background="white"):
    """Save shapes to SVG file."""
    import logging
    import sys

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    try:
        svg_content = export_svg(shapes, width, height, background)
        logging.info(
            "svg_export.save_svg: writing '%s' (%d bytes)", filepath, len(svg_content)
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)
        logging.info("svg_export.save_svg: success writing '%s'", filepath)
        return True
    except Exception:
        logging.exception("svg_export.save_svg: failed writing '%s'", filepath)
        return False


# Compatibility aliases
write_svg = save_svg
export_shapes_to_svg = export_svg


# Add: simple, robust SVG shape counter used by CLI/tests
def count_svg_shapes(svg_source) -> int:
    """
    Count common SVG shape elements in either a file path or a raw SVG string.
    Returns the total number of shape tags found (circle, path, rect, ellipse, polygon, polyline).
    This is intentionally simple (regex-based) and tolerant of encoding errors.
    """
    import re
    from pathlib import Path

    try:
        # If svg_source points to an existing file, read it; otherwise treat as string content
        if isinstance(svg_source, (str, Path)) and Path(svg_source).exists():
            text = Path(svg_source).read_text(encoding="utf-8", errors="ignore")
        else:
            text = str(svg_source or "")
    except Exception:
        text = str(svg_source or "")

    # Count occurrences of opening tags for common shapes
    tags = ["circle", "path", "rect", "ellipse", "polygon", "polyline"]
    total = 0
    for t in tags:
        try:
            total += len(
                re.findall(
                    r"<\s*" + re.escape(t) + r"[\s>/]", text, flags=re.IGNORECASE
                )
            )
        except Exception:
            # be defensive; if regex fails for any reason, skip that tag
            continue
    return total
