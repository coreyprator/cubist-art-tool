#!/usr/bin/env python3
"""
SVG Export System with Metadata Integration
Provides export_svg function with Adobe XMP-compatible metadata embedding.
"""

# Import metadata system
try:
    from svg_metadata import generate_xmp_metadata
except ImportError:
    generate_xmp_metadata = None


def _to_rgb_string(val):
    """Normalize color spec to CSS rgb(r,g,b) or pass-through strings."""
    if val is None:
        return None
    if isinstance(val, (list, tuple)) and len(val) >= 3:
        try:
            r, g, b = int(val[0]), int(val[1]), int(val[2])
            return f"rgb({r},{g},{b})"
        except Exception:
            return str(val)
    if isinstance(val, str):
        s = val.strip()
        if s.startswith("(") and s.endswith(")"):
            parts = s[1:-1].split(",")
            if len(parts) >= 3:
                try:
                    r, g, b = [int(float(p.strip())) for p in parts[:3]]
                    return f"rgb({r},{g},{b})"
                except Exception:
                    pass
        return s
    return str(val)


def export_svg(
    shapes,
    width=800,
    height=600,
    background="white",
    metadata=None
):
    """
    Export shapes to SVG format with optional metadata embedding.

    Args:
        shapes: List of shape dictionaries
        width, height: Canvas dimensions
        background: Background color
        metadata: Optional metadata dictionary with keys:
            - geometry: str
            - fill_method: str
            - input_source: str
            - target_shapes: int
            - seed: int
            - generation_time: float
            - parameters: Dict[str, float]

    Returns:
        str: SVG content as string
    """

    svg_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
    ]
    
    # Add metadata if provided and metadata system available
    if metadata and generate_xmp_metadata:
        try:
            xmp_metadata = generate_xmp_metadata(
                geometry=metadata.get("geometry", "unknown"),
                fill_method=metadata.get("fill_method", "default"),
                input_source=metadata.get("input_source", ""),
                canvas_width=width,
                canvas_height=height,
                target_shapes=metadata.get("target_shapes", len(shapes)),
                actual_shapes=len(shapes),
                seed=metadata.get("seed", 42),
                shapes=shapes,
                generation_time=metadata.get("generation_time", 0.0),
                parameters=metadata.get("parameters", {})
            )
            svg_parts.append(xmp_metadata)
        except Exception as e:
            print(f"Warning: Failed to generate metadata: {e}")
    
    svg_parts.append(f'<rect width="100%" height="100%" fill="{background}"/>')
    
    shape_count = 0
    for shape in shapes:
        if not isinstance(shape, dict):
            continue
        shape_count += 1
        shape_type = shape.get("type", "").lower()
        
        # Normalize fill/stroke
        fill_raw = shape.get("fill", None)
        stroke_raw = shape.get("stroke", None)
        fill_color = _to_rgb_string(fill_raw) or f"hsl({(shape_count*137)%360},70%,50%)"
        stroke_color = _to_rgb_string(stroke_raw) or "none"
        stroke_width = shape.get("stroke-width", shape.get("stroke_width", 0.5))
        
        # Get opacity from shape, default to 0.7
        opacity = shape.get("opacity", 0.7)
        
        # Circle handling
        if shape_type == "circle":
            cx = shape.get("cx", 0)
            cy = shape.get("cy", 0)
            r = shape.get("r", 1)
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_width}" '
                f'opacity="{opacity}"/>'
            )
            continue
        
        points = shape.get("points", [])
        if not points:
            continue
        
        # Triangles
        if shape_type == "triangle" and len(points) >= 3:
            pts = points[:3]
            path_data = f"M {pts[0][0]},{pts[0][1]} L {pts[1][0]},{pts[1][1]} L {pts[2][0]},{pts[2][1]} Z"
            svg_parts.append(
                f'<path d="{path_data}" fill="{fill_color}" stroke="{stroke_color}" '
                f'stroke-width="{stroke_width}" opacity="{opacity}"/>'
            )
            continue
        
        # Generic polygon
        points_str = " ".join(f"{int(p[0])},{int(p[1])}" for p in points)
        svg_parts.append(
            f'<polygon points="{points_str}" fill="{fill_color}" stroke="{stroke_color}" '
            f'stroke-width="{stroke_width}" opacity="{opacity}"/>'
        )

    svg_parts.append("</svg>")

    print(f"SVG export: exported {shape_count} shapes with metadata")
    return "\n".join(svg_parts)


def save_svg(
    shapes,
    filepath,
    width=800,
    height=600,
    background="white",
    metadata=None
):
    """Save shapes to SVG file with optional metadata."""
    import logging
    import sys

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    try:
        svg_content = export_svg(shapes, width, height, background, metadata)
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


# SVG shape counter
def count_svg_shapes(svg_source) -> int:
    """
    Count common SVG shape elements.
    """
    import re
    from pathlib import Path

    try:
        if isinstance(svg_source, (str, Path)) and Path(svg_source).exists():
            text = Path(svg_source).read_text(encoding="utf-8", errors="ignore")
        else:
            text = str(svg_source or "")
    except Exception:
        text = str(svg_source or "")

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
            continue
    return total