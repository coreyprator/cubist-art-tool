# geometry_plugins/delaunay.py - Enhanced with Parameter Registry Integration
# Cubist Art v2.5.0 - Phase 1 Complete

from __future__ import annotations

import math
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

PLUGIN_NAME = "delaunay"


def generate(
    canvas_size: Tuple[int, int],
    total_points: int = 256,
    seed: int = 0,
    seed_points: Optional[List[Tuple[float, float]]] = None,
    input_image=None,
    cascade_fill_enabled: bool = False,
    cascade_intensity: float = None,
    opacity: float = None,
    min_triangle_size: float = 3.0,
    max_placement_attempts: int = 50,
    verbose: bool = False,
    **params,
) -> List[Dict]:
    """
    Enhanced Delaunay Triangulation with Parameter Registry Integration

    Parameters:
    - cascade_fill_enabled: Enable universal cascade fill system
    - cascade_intensity: How aggressively to fill gaps (0.1-1.0, default: 0.8)
    - opacity: Shape transparency (0.1-1.0, default: 0.7)
    """
    
    # Apply defaults from parameter registry
    if cascade_intensity is None:
        cascade_intensity = get_parameter_default("delaunay", "cascade_intensity")
    else:
        valid, clamped, msg = validate_parameter("delaunay", "cascade_intensity", cascade_intensity)
        if not valid and verbose:
            print(f"[delaunay] Parameter validation: {msg}, using {clamped}")
        cascade_intensity = clamped
    
    if opacity is None:
        opacity = get_parameter_default("delaunay", "opacity")
    else:
        valid, clamped, msg = validate_parameter("delaunay", "opacity", opacity)
        if not valid and verbose:
            print(f"[delaunay] Parameter validation: {msg}, using {clamped}")
        opacity = clamped
    
    width, height = canvas_size
    rng = random.Random(int(seed))

    if verbose:
        print(f"[delaunay] Delaunay generation - Cascade: {'ENABLED' if cascade_fill_enabled else 'DISABLED'}")
        print(f"[delaunay] Canvas: {width}x{height}, Target: {total_points} triangles")
        print(f"[delaunay] Parameters: cascade_intensity={cascade_intensity}, opacity={opacity}")

    # Phase 1: Generate base triangulation
    if cascade_fill_enabled:
        base_count = max(int(total_points * 0.6), 8)
        if verbose:
            print(f"[delaunay] Cascade mode: generating {base_count} base triangles, {total_points - base_count} cascade")
    else:
        base_count = total_points
        if verbose:
            print(f"[delaunay] Default mode: generating {base_count} triangles")

    # Generate base triangulation with opacity
    base_shapes = _generate_base_triangulation(
        canvas_size, base_count, seed, seed_points, input_image, opacity, verbose
    )

    if verbose:
        print(f"[delaunay] Generated {len(base_shapes)} base triangles")

    # Phase 2: Apply cascade fill if enabled
    final_shapes = base_shapes

    if cascade_fill_enabled and len(base_shapes) < total_points:
        if verbose:
            print(f"[delaunay] Applying universal cascade fill (intensity: {cascade_intensity})")

        # Calculate average triangle size for cascade reference
        avg_triangle_size = _calculate_average_triangle_size(base_shapes)
        cascade_size = max(min_triangle_size, avg_triangle_size * cascade_intensity * 0.4)

        # Create shape generator for cascade triangles
        def generate_cascade_triangle() -> Dict:
            side_length = rng.uniform(cascade_size * 0.7, cascade_size * 1.3)
            height_tri = side_length * math.sqrt(3) / 2

            points = [
                (0.0, 0.0),
                (side_length, 0.0),
                (side_length / 2, height_tri),
            ]

            return {
                "type": "polygon",
                "points": points,
                "fill": "rgb(128,128,128)",
                "stroke": (0, 0, 0),
                "stroke_width": 0.3,
                "opacity": opacity,  # Add opacity to cascade shapes
            }

        # Apply universal cascade fill
        enhanced_shapes = apply_universal_cascade_fill(
            shapes=base_shapes,
            canvas_size=canvas_size,
            target_count=total_points,
            shape_generator=generate_cascade_triangle,
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
                color_rgb = _sample_image_color(input_image, centroid_x, centroid_y, width, height)
                shape["fill"] = color_rgb

        final_shapes = enhanced_shapes

        if verbose:
            print(f"[delaunay] Universal cascade fill added {len(cascade_shapes)} triangles")

    # Canonicalize final results
    result = _canonicalize_triangles(final_shapes)

    # Calculate final statistics
    if verbose:
        total_area = sum(
            _calculate_triangle_area(shape["points"])
            for shape in result
            if shape.get("type") == "polygon" and "points" in shape
        )
        canvas_area = width * height
        coverage = (total_area / canvas_area) * 100

        print(f"[delaunay] Final count: {len(result)} triangles")
        print(f"[delaunay] Canvas coverage: {coverage:.1f}%")
        print(f"[delaunay] Mode: {'CASCADE FILL' if cascade_fill_enabled else 'DEFAULT'}")

    return result


def _generate_base_triangulation(
    canvas_size: Tuple[int, int],
    point_count: int,
    seed: int,
    seed_points: Optional[List[Tuple[float, float]]],
    input_image,
    opacity: float,
    verbose: bool = False
) -> List[Dict]:
    """Generate base Delaunay triangulation with opacity."""
    width, height = canvas_size
    rng = random.Random(int(seed))

    if seed_points and len(seed_points) >= 3:
        pts = [tuple(map(float, pt)) for pt in seed_points]
        if verbose:
            print(f"[delaunay] Using {len(pts)} provided seed points")
    else:
        n = max(3, int(point_count))
        pts = [(rng.uniform(0, width), rng.uniform(0, height)) for _ in range(n)]
        if verbose:
            print(f"[delaunay] Generated {len(pts)} random seed points")

    try:
        import numpy as _np
        from scipy.spatial import Delaunay as _Delaunay

        if verbose:
            print("[delaunay] Using SciPy Delaunay triangulation")

        tri = _Delaunay(_np.array(pts, dtype=float))
        shapes: List[Dict] = []

        for simplex in tri.simplices:
            p0 = tuple(map(float, tri.points[simplex[0]]))
            p1 = tuple(map(float, tri.points[simplex[1]]))
            p2 = tuple(map(float, tri.points[simplex[2]]))

            centroid_x = (p0[0] + p1[0] + p2[0]) / 3
            centroid_y = (p0[1] + p1[1] + p2[1]) / 3

            shapes.append({
                "type": "polygon",
                "points": [p0, p1, p2],
                "fill": _sample_image_color(
                    input_image, centroid_x, centroid_y, width, height
                ),
                "stroke": (0, 0, 0),
                "stroke_width": 0.5,
                "opacity": opacity,  # Add opacity to base shapes
            })

        return shapes

    except Exception as e:
        if verbose:
            print(f"[delaunay] SciPy not available ({e}), using grid fallback")

        shapes = _grid_fallback_tris(width, height, rng, input_image, opacity)
        return shapes


def _grid_fallback_tris(
    width: int, height: int, rng: random.Random, input_image=None, opacity: float = 0.7
) -> List[Dict]:
    """Build a jittered grid and triangulate each cell."""
    nx = max(3, int(round(math.sqrt(64))))
    ny = nx
    dx = width / (nx - 1)
    dy = height / (ny - 1)
    jitter = 0.20 * min(dx, dy)

    verts: List[Tuple[float, float]] = []
    for j in range(ny):
        for i in range(nx):
            x = i * dx + rng.uniform(-jitter, jitter)
            y = j * dy + rng.uniform(-jitter, jitter)
            verts.append(
                (float(max(0.0, min(width, x))), float(max(0.0, min(height, y))))
            )

    def vid(i: int, j: int) -> int:
        return j * nx + i

    shapes: List[Dict] = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = verts[vid(i, j)]
            b = verts[vid(i + 1, j)]
            c = verts[vid(i, j + 1)]
            d = verts[vid(i + 1, j + 1)]
            tris = (
                [(a, b, d), (a, d, c)] if ((i + j) % 2 == 0) else [(a, b, c), (b, d, c)]
            )
            for t in tris:
                centroid_x = (t[0][0] + t[1][0] + t[2][0]) / 3
                centroid_y = (t[0][1] + t[1][1] + t[2][1]) / 3

                shapes.append({
                    "type": "polygon",
                    "points": [
                        (float(t[0][0]), float(t[0][1])),
                        (float(t[1][0]), float(t[1][1])),
                        (float(t[2][0]), float(t[2][1])),
                    ],
                    "fill": _sample_image_color(
                        input_image, centroid_x, centroid_y, width, height
                    ),
                    "stroke": (0, 0, 0),
                    "stroke_width": 0.5,
                    "opacity": opacity,  # Add opacity
                })
    return shapes


def _calculate_average_triangle_size(shapes: List[Dict]) -> float:
    """Calculate average triangle size (edge length)."""
    if not shapes:
        return 10.0

    total_perimeter = 0.0
    count = 0

    for shape in shapes:
        if shape.get("type") == "polygon" and "points" in shape:
            points = shape["points"]
            if len(points) >= 3:
                p1, p2, p3 = points[0], points[1], points[2]

                edge1 = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                edge2 = math.sqrt((p3[0] - p2[0])**2 + (p3[1] - p2[1])**2)
                edge3 = math.sqrt((p1[0] - p3[0])**2 + (p1[1] - p3[1])**2)

                perimeter = edge1 + edge2 + edge3
                total_perimeter += perimeter
                count += 1

    if count > 0:
        avg_perimeter = total_perimeter / count
        return avg_perimeter / 3
    else:
        return 10.0


def _calculate_triangle_area(points: List[Tuple[float, float]]) -> float:
    """Calculate area of triangle given three points."""
    if len(points) < 3:
        return 0.0

    p1, p2, p3 = points[:3]
    return abs((p1[0]*(p2[1] - p3[1]) + p2[0]*(p3[1] - p1[1]) + p3[0]*(p1[1] - p2[1])) / 2.0)


def _sample_image_color(
    input_image, x: float, y: float, canvas_width: int, canvas_height: int
) -> Tuple[int, int, int]:
    """Sample color from input image."""
    if input_image is None:
        return (128, 128, 128)

    try:
        img_width, img_height = input_image.size
        img_x = int((x / canvas_width) * img_width)
        img_y = int((y / canvas_height) * img_height)
        img_x = max(0, min(img_width - 1, img_x))
        img_y = max(0, min(img_height - 1, img_y))
        pixel = input_image.getpixel((img_x, img_y))

        if isinstance(pixel, tuple):
            if len(pixel) >= 3:
                return (int(pixel[0]), int(pixel[1]), int(pixel[2]))
            elif len(pixel) == 1:
                return (int(pixel[0]), int(pixel[0]), int(pixel[0]))
        else:
            return (int(pixel), int(pixel), int(pixel))

    except Exception:
        return (128, 128, 128)

    return (128, 128, 128)


def _canonicalize_triangles(shapes: List[Dict]) -> List[Dict]:
    """Stable ordering by centroid and vertex list."""
    def key(shape: Dict):
        pts = shape.get("points", [])
        vs = sorted((float(x), float(y)) for x, y in pts)
        cx = round(sum(x for x, _ in vs) / 3.0, 3)
        cy = round(sum(y for _, y in vs) / 3.0, 3)
        flat = tuple(round(v, 3) for xy in vs for v in xy)
        return (cx, cy, flat)

    return sorted(shapes, key=key)


def register(register_fn) -> None:
    """Register this plugin with the geometry system."""
    register_fn(PLUGIN_NAME, generate)