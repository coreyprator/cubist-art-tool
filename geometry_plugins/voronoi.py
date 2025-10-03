# geometry_plugins/voronoi.py - Enhanced with Parameter Registry Integration
# Cubist Art v2.5.0 - Phase 1 Complete

from __future__ import annotations

import random
from typing import Dict, List, Tuple, Optional

# Import universal cascade fill system
try:
    from cascade_fill_system import apply_universal_cascade_fill, sample_image_color
except ImportError:
    def apply_universal_cascade_fill(shapes, canvas_size, target_count, shape_generator, seed=42, verbose=False):
        return shapes
    def sample_image_color(input_image, x, y, canvas_width, canvas_height):
        return "rgb(128,128,128)"

# Import parameter registry
try:
    from geometry_parameters import get_parameter_default, validate_parameter
except ImportError:
    def get_parameter_default(geometry, param):
        defaults = {
            "cascade_intensity": 0.8,
            "opacity": 0.7
        }
        return defaults.get(param)
    
    def validate_parameter(geometry, param, value):
        return True, value, ""

PLUGIN_NAME = "voronoi"


def generate(
    canvas_size: Tuple[int, int],
    total_points: int = 128,
    seed: int = 0,
    seed_points: Optional[List[Tuple[float, float]]] = None,
    input_image=None,
    cascade_fill_enabled: bool = False,
    cascade_intensity: float = None,
    opacity: float = None,
    verbose: bool = False,
    **params,
) -> List[Dict]:
    """
    Voronoi Diagram with Parameter Registry Integration

    Parameters:
    - cascade_fill_enabled: Enable cascade fill system
    - cascade_intensity: How aggressively to fill gaps (0.1-1.0, default: 0.8)
    - opacity: Shape transparency (0.1-1.0, default: 0.7)
    """
    
    # Apply defaults from parameter registry
    if cascade_intensity is None:
        cascade_intensity = get_parameter_default("voronoi", "cascade_intensity")
    else:
        valid, clamped, msg = validate_parameter("voronoi", "cascade_intensity", cascade_intensity)
        if not valid and verbose:
            print(f"[voronoi] Parameter validation: {msg}, using {clamped}")
        cascade_intensity = clamped
    
    if opacity is None:
        opacity = get_parameter_default("voronoi", "opacity")
    else:
        valid, clamped, msg = validate_parameter("voronoi", "opacity", opacity)
        if not valid and verbose:
            print(f"[voronoi] Parameter validation: {msg}, using {clamped}")
        opacity = clamped
    
    width, height = canvas_size
    rng = random.Random(int(seed))

    if verbose:
        print(f"[voronoi] Voronoi generation - Cascade: {'ENABLED' if cascade_fill_enabled else 'DISABLED'}")
        print(f"[voronoi] Canvas: {width}x{height}, Target: {total_points} cells")
        print(f"[voronoi] Parameters: cascade_intensity={cascade_intensity}, opacity={opacity}")

    # Determine base count
    if cascade_fill_enabled:
        base_count = max(int(total_points * 0.6), 8)
        if verbose:
            print(f"[voronoi] Cascade mode: generating {base_count} base cells, {total_points - base_count} cascade")
    else:
        base_count = total_points
        if verbose:
            print(f"[voronoi] Default mode: generating {base_count} cells")

    # Generate seed points
    if seed_points and len(seed_points) >= 3:
        pts = [tuple(map(float, pt)) for pt in seed_points]
        if verbose:
            print(f"[voronoi] Using {len(pts)} provided seed points")
    else:
        pts = [
            (rng.uniform(0, width), rng.uniform(0, height))
            for _ in range(max(3, int(base_count)))
        ]
        if verbose:
            print(f"[voronoi] Generated {len(pts)} random seed points")

    # Generate base Voronoi diagram with opacity
    base_shapes = []
    try:
        import numpy as _np
        from scipy.spatial import Voronoi as _Voronoi

        if verbose:
            print("[voronoi] Using SciPy Voronoi diagram")

        v = _Voronoi(_np.array(pts, dtype=float))
        regions = _voronoi_finite_polygons_2d(v)

        for region, site_idx in regions:
            poly = _clip_poly_to_bbox(region, (0.0, 0.0, float(width), float(height)))
            if len(poly) >= 3:
                centroid_x = sum(x for x, y in poly) / len(poly)
                centroid_y = sum(y for x, y in poly) / len(poly)

                base_shapes.append({
                    "type": "polygon",
                    "points": [(float(x), float(y)) for x, y in poly],
                    "fill": _sample_image_color(
                        input_image, centroid_x, centroid_y, width, height
                    ),
                    "stroke": "none",
                    "stroke_width": 0,
                    "opacity": opacity,  # Add opacity to base shapes
                })

        if verbose:
            print(f"[voronoi] Generated {len(base_shapes)} Voronoi polygons")

    except Exception as e:
        if verbose:
            print(f"[voronoi] SciPy Voronoi failed ({e}), using circle fallback")

        radius = max(1.0, 0.0075 * min(width, height))
        base_shapes = [
            {
                "type": "circle",
                "cx": float(x),
                "cy": float(y),
                "r": float(radius),
                "fill": _sample_image_color(input_image, x, y, width, height),
                "stroke": "none",
                "stroke_width": 0,
                "opacity": opacity,  # Add opacity to fallback circles
            }
            for (x, y) in pts
        ]
        if verbose:
            print(f"[voronoi] Generated {len(base_shapes)} fallback circles")

    # Apply cascade fill if enabled
    final_shapes = base_shapes

    if (cascade_fill_enabled and len(base_shapes) < total_points and
        base_shapes and base_shapes[0].get("type") == "polygon"):

        if verbose:
            print(f"[voronoi] Applying cascade fill to Voronoi polygons")

        def generate_cascade_cell() -> Dict:
            size = rng.uniform(8, 20)
            return {
                "type": "polygon",
                "points": [(0.0, 0.0), (size, 0.0), (size, size), (0.0, size)],
                "fill": "rgb(128,128,128)",
                "stroke": "none",
                "stroke_width": 0,
                "opacity": opacity,  # Add opacity to cascade shapes
            }

        enhanced_shapes = apply_universal_cascade_fill(
            shapes=base_shapes,
            canvas_size=canvas_size,
            target_count=total_points,
            shape_generator=generate_cascade_cell,
            seed=seed + 1000,
            verbose=verbose
        )

        # Update colors for cascade shapes
        cascade_shapes = enhanced_shapes[len(base_shapes):]
        for shape in cascade_shapes:
            if shape.get("type") == "polygon" and "points" in shape:
                points = shape["points"]
                centroid_x = sum(p[0] for p in points) / len(points)
                centroid_y = sum(p[1] for p in points) / len(points)
                color = _sample_image_color(input_image, centroid_x, centroid_y, width, height)
                shape["fill"] = color

        final_shapes = enhanced_shapes

        if verbose:
            print(f"[voronoi] Cascade fill added {len(cascade_shapes)} shapes")
    elif cascade_fill_enabled and base_shapes and base_shapes[0].get("type") == "circle":
        if verbose:
            print(f"[voronoi] Cascade fill skipped - Voronoi fell back to circles")
    elif cascade_fill_enabled:
        if verbose:
            print(f"[voronoi] Cascade fill skipped - target already reached or no shapes")

    # Sort results
    if final_shapes:
        def vkey(s):
            if s.get("type") == "polygon":
                pts = s.get("points", [])
                cx = round(sum(x for x, _ in pts) / max(1, len(pts)), 3)
                cy = round(sum(y for _, y in pts) / max(1, len(pts)), 3)
                return (cx, cy)
            elif s.get("type") == "circle":
                return (round(s.get("cx", 0), 3), round(s.get("cy", 0), 3))
            return (0, 0)

        final_shapes = sorted(final_shapes, key=vkey)

    if verbose:
        shape_types = {}
        for shape in final_shapes:
            shape_type = shape.get("type", "unknown")
            shape_types[shape_type] = shape_types.get(shape_type, 0) + 1

        print(f"[voronoi] Final count: {len(final_shapes)} shapes")
        for shape_type, count in shape_types.items():
            print(f"[voronoi]   {count} {shape_type}s")
        print(f"[voronoi] Mode: {'CASCADE FILL' if cascade_fill_enabled else 'DEFAULT'}")

    return final_shapes


def _sample_image_color(
    input_image, x: float, y: float, canvas_width: int, canvas_height: int
) -> str:  # CHANGED: was Tuple[int, int, int]
    """Sample color from input image and return SVG-compatible color string."""
    if input_image is None:
        return "rgb(128, 128, 128)"  # CHANGED: was (128, 128, 128)

    try:
        img_width, img_height = input_image.size
        img_x = int((x / canvas_width) * img_width)
        img_y = int((y / canvas_height) * img_height)
        img_x = max(0, min(img_width - 1, img_x))
        img_y = max(0, min(img_height - 1, img_y))
        pixel = input_image.getpixel((img_x, img_y))

        if isinstance(pixel, tuple):
            if len(pixel) >= 3:
                r, g, b = int(pixel[0]), int(pixel[1]), int(pixel[2])
                return f"rgb({r}, {g}, {b})"  # CHANGED: was (r, g, b)
            elif len(pixel) == 1:
                gray = int(pixel[0])
                return f"rgb({gray}, {gray}, {gray})"  # CHANGED: was (gray, gray, gray)
        else:
            gray = int(pixel)
            return f"rgb({gray}, {gray}, {gray})"  # CHANGED: was (gray, gray, gray)

    except Exception:
        return "rgb(128, 128, 128)"  # CHANGED: was (128, 128, 128)

    return "rgb(128, 128, 128)"  # CHANGED: was (128, 128, 128)


def _voronoi_finite_polygons_2d(voronoi) -> List[Tuple[List[Tuple[float, float]], int]]:
    """Generate finite Voronoi polygons from scipy Voronoi object."""
    import numpy as np

    shapes = []
    center = voronoi.points.mean(axis=0)
    radius = np.ptp(voronoi.points, axis=0).max() * 2
    
    for point_idx, region_idx in enumerate(voronoi.point_region):
        vertices = voronoi.regions[region_idx]
        if -1 not in vertices and vertices:
            poly = [
                (float(voronoi.vertices[v][0]), float(voronoi.vertices[v][1]))
                for v in vertices
            ]
            shapes.append((poly, point_idx))
            continue
            
        ridges = [r for r in voronoi.ridge_dict.keys() if point_idx in r]
        new_vertices = []
        for p1, p2 in ridges:
            if p2 == point_idx:
                p1, p2 = p2, p1
            vkey = (p1, p2)
            ridge_vertices = voronoi.ridge_dict.get(vkey)
            if ridge_vertices is None:
                continue
            v1, v2 = ridge_vertices
            if v1 >= 0 and v2 >= 0:
                new_vertices.extend([v1, v2])
                continue
            t = voronoi.points[p2] - voronoi.points[p1]
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])
            midpoint = voronoi.points[[p1, p2]].mean(axis=0)
            direction = np.sign((midpoint - center).dot(n)) * n
            far_point = voronoi.vertices[v1 if v1 >= 0 else v2] + direction * radius
            new_vertices.append(v1 if v1 >= 0 else v2)
            voronoi.vertices = np.vstack([voronoi.vertices, far_point])
            new_vertices.append(len(voronoi.vertices) - 1)
            
        vs = np.unique(new_vertices).astype(int)
        pts = voronoi.vertices[vs]
        c = pts.mean(axis=0)
        angles = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
        order = np.argsort(angles)
        poly = [(float(pts[i][0]), float(pts[i][1])) for i in order]
        shapes.append((poly, point_idx))
    return shapes


def _clip_poly_to_bbox(
    poly: List[Tuple[float, float]],
    bbox: Tuple[float, float, float, float],
) -> List[Tuple[float, float]]:
    """Clip polygon to bounding box using Sutherland-Hodgman algorithm."""
    xmin, ymin, xmax, ymax = bbox

    def inside(p, edge):
        x, y = p
        if edge == 0:
            return x >= xmin
        if edge == 1:
            return x <= xmax
        if edge == 2:
            return y >= ymin
        if edge == 3:
            return y <= ymax

    def intersect(p1, p2, edge):
        x1, y1 = p1
        x2, y2 = p2
        if x1 == x2 and y1 == y2:
            return (x1, y1)
        if edge in (0, 1):
            x_edge = xmin if edge == 0 else xmax
            t = (x_edge - x1) / (x2 - x1)
            return (x_edge, y1 + t * (y2 - y1))
        else:
            y_edge = ymin if edge == 2 else ymax
            t = (y_edge - y1) / (y2 - y1)
            return (x1 + t * (x2 - x1), y_edge)

    output = poly[:]
    for edge in range(4):
        input_list = output
        output = []
        if not input_list:
            break
        s = input_list[-1]
        for e in input_list:
            if inside(e, edge):
                if not inside(s, edge):
                    output.append(intersect(s, e, edge))
                output.append(e)
            elif inside(s, edge):
                output.append(intersect(s, e, edge))
            s = e
    return output


def register(register_fn) -> None:
    register_fn(PLUGIN_NAME, generate)