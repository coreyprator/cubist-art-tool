#!/usr/bin/env python3
"""
SVG Export Fallback System
Provides export_svg function as last resort when plugins don't have exporters.
"""


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
        shape_count += 1
        if not isinstance(shape, dict):
            continue

        shape_type = shape.get("type", "").lower()

        # Handle circle shapes
        if shape_type == "circle":
            cx = shape.get("cx", 0)
            cy = shape.get("cy", 0)
            r = shape.get("r", 1)
            fill = shape.get("fill", f"hsl({(shape_count * 137) % 360}, 70%, 50%)")
            stroke = shape.get("stroke", "none")
            stroke_width = shape.get("stroke-width", shape.get("stroke_width", 1))

            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
            )
            continue

        # Existing triangle/polygon handling
        points = shape.get("points", [])
        if not points:
            continue

        # Generate a color based on shape index for variety
        if not shape.get("fill"):
            hue = (shape_count * 137) % 360
            fill_color = f"hsl({hue}, 70%, 50%)"
        else:
            fill_color = shape["fill"]

        if shape_type == "triangle" and len(points) >= 3:
            path_data = f"M {points[0][0]},{points[0][1]}"
            for point in points[1:3]:
                path_data += f" L {point[0]},{point[1]}"
            path_data += " Z"

            svg_parts.append(
                f'<path d="{path_data}" fill="{fill_color}" stroke="{stroke_color}" stroke-width="1" opacity="0.7"/>'
            )
            shape_count += 1

        elif shape_type in ["polygon", "poly"] and len(points) >= 3:
            points_str = " ".join(f"{p[0]},{p[1]}" for p in points)
            svg_parts.append(
                f'<polygon points="{points_str}" fill="{fill_color}" stroke="{stroke_color}" stroke-width="1" opacity="0.7"/>'
            )
            shape_count += 1

        elif len(points) >= 3:
            # Generic polygon fallback for any multi-point shape
            points_str = " ".join(f"{p[0]},{p[1]}" for p in points)
            svg_parts.append(
                f'<polygon points="{points_str}" fill="{fill_color}" stroke="{stroke_color}" stroke-width="1" opacity="0.7"/>'
            )
            shape_count += 1

    svg_parts.append("</svg>")

    print(f"SVG export fallback: exported {shape_count} shapes")
    return "\n".join(svg_parts)


def save_svg(shapes, filepath, width=800, height=600, background="white"):
    """Save shapes to SVG file."""
    try:
        svg_content = export_svg(shapes, width, height, background)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)
        return True
    except Exception as e:
        print(f"Failed to save SVG to {filepath}: {e}")
        return False


# Compatibility aliases
write_svg = save_svg
export_shapes_to_svg = export_svg
