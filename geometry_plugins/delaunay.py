# geometry_plugins/delaunay.py - Enhanced with Universal Cascade Fill
# Cubist Art v2.5.0 - Priority 1 Implementation

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple, Optional

# Import universal cascade fill system
try:
    from cascade_fill_system import apply_universal_cascade_fill, sample_image_color
except ImportError:
    # Fallback if cascade system not available
    def apply_universal_cascade_fill(shapes, canvas_size, target_count, shape_generator, seed=42, verbose=False):
        return shapes
    def sample_image_color(input_image, x, y, canvas_width, canvas_height):
        return "rgb(128,128,128)"

PLUGIN_NAME = "delaunay"


def generate(
    canvas_size: Tuple[int, int],
    total_points: int = 256,
    seed: int = 0,
    seed_points: Optional[List[Tuple[float, float]]] = None,
    input_image=None,
    cascade_fill_enabled: bool = False,
    cascade_intensity: float = 0.8,
    min_triangle_size: float = 3.0,
    max_placement_attempts: int = 50,
    verbose: bool = False,
    **params,
) -> List[Dict]:
    """
    Enhanced Delaunay Triangulation with Universal Cascade Fill Integration
    
    Parameters:
    - cascade_fill_enabled: Enable universal cascade fill system (default: False for backward compatibility)
    - cascade_intensity: How aggressively to fill gaps (0.0-1.0, default: 0.8)
    - min_triangle_size: Minimum triangle edge length for cascade shapes (default: 3.0)
    - max_placement_attempts: Maximum attempts for cascade placement (default: 50)
    """
    width, height = canvas_size
    rng = random.Random(int(seed))
    
    if verbose:
        print(f"[delaunay] Delaunay generation - Cascade: {'ENABLED' if cascade_fill_enabled else 'DISABLED'}")
        print(f"[delaunay] Canvas: {width}x{height}, Target: {total_points} triangles")
    
    # Phase 1: Generate base triangulation (60-70% of target if cascade enabled)
    if cascade_fill_enabled:
        base_count = max(int(total_points * 0.6), 8)  # 60% for base when cascade enabled
        if verbose:
            print(f"[delaunay] Cascade mode: generating {base_count} base triangles, {total_points - base_count} cascade")
    else:
        base_count = total_points  # All triangles in default mode
        if verbose:
            print(f"[delaunay] Default mode: generating {base_count} triangles")
    
    # Generate base triangulation
    base_shapes = _generate_base_triangulation(
        canvas_size, base_count, seed, seed_points, input_image, verbose
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
            # Generate small equilateral triangle for gap filling
            side_length = rng.uniform(cascade_size * 0.7, cascade_size * 1.3)
            height_tri = side_length * math.sqrt(3) / 2
            
            # Create equilateral triangle at origin - cascade system will position it
            points = [
                (0.0, 0.0),
                (side_length, 0.0),
                (side_length / 2, height_tri),
            ]
            
            return {
                "type": "polygon",
                "points": points,
                "fill": "rgb(128,128,128)",  # Placeholder color
                "stroke": (0, 0, 0),
                "stroke_width": 0.3,  # Thinner stroke for cascade triangles
            }
        
        # Apply universal cascade fill
        enhanced_shapes = apply_universal_cascade_fill(
            shapes=base_shapes,
            canvas_size=canvas_size,
            target_count=total_points,
            shape_generator=generate_cascade_triangle,
            seed=seed + 1000,  # Different seed for cascade
            verbose=verbose
        )
        
        # Update colors for cascade shapes based on their final positions
        cascade_shapes = enhanced_shapes[len(base_shapes):]
        for shape in cascade_shapes:
            if shape.get("type") == "polygon" and "points" in shape:
                points = shape["points"]
                # Calculate centroid
                centroid_x = sum(p[0] for p in points) / len(points)
                centroid_y = sum(p[1] for p in points) / len(points)
                # Sample color at final position
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
    verbose: bool = False
) -> List[Dict]:
    """Generate base Delaunay triangulation."""
    width, height = canvas_size
    rng = random.Random(int(seed))

    # Use provided seeds if available, otherwise sample uniformly
    if seed_points and len(seed_points) >= 3:
        pts = [tuple(map(float, pt)) for pt in seed_points]
        if verbose:
            print(f"[delaunay] Using {len(pts)} provided seed points")
    else:
        n = max(3, int(point_count))
        pts = [(rng.uniform(0, width), rng.uniform(0, height)) for _ in range(n)]
        if verbose:
            print(f"[delaunay] Generated {len(pts)} random seed points")

    # Prefer SciPy Delaunay; otherwise use jittered grid fallback
    try:
        import numpy as _np
        from scipy.spatial import Delaunay as _Delaunay  # type: ignore

        if verbose:
            print("[delaunay] Using SciPy Delaunay triangulation")
        
        tri = _Delaunay(_np.array(pts, dtype=float))
        shapes: List[Dict] = []
        
        for simplex in tri.simplices:
            p0 = tuple(map(float, tri.points[simplex[0]]))
            p1 = tuple(map(float, tri.points[simplex[1]]))
            p2 = tuple(map(float, tri.points[simplex[2]]))

            # Calculate triangle centroid for color sampling
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
            })
        
        return shapes
        
    except Exception as e:
        if verbose:
            print(f"[delaunay] SciPy not available ({e}), using grid fallback")
        
        shapes = _grid_fallback_tris(width, height, rng, input_image)
        return shapes


def _calculate_average_triangle_size(shapes: List[Dict]) -> float:
    """Calculate average triangle size (edge length) from triangles."""
    if not shapes:
        return 10.0  # Default fallback
    
    total_perimeter = 0.0
    count = 0
    
    for shape in shapes:
        if shape.get("type") == "polygon" and "points" in shape:
            points = shape["points"]
            if len(points) >= 3:
                p1, p2, p3 = points[0], points[1], points[2]
                
                # Calculate perimeter
                edge1 = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                edge2 = math.sqrt((p3[0] - p2[0])**2 + (p3[1] - p2[1])**2)
                edge3 = math.sqrt((p1[0] - p3[0])**2 + (p1[1] - p3[1])**2)
                
                perimeter = edge1 + edge2 + edge3
                total_perimeter += perimeter
                count += 1
    
    if count > 0:
        avg_perimeter = total_perimeter / count
        return avg_perimeter / 3  # Average edge length
    else:
        return 10.0


def _calculate_triangle_area(points: List[Tuple[float, float]]) -> float:
    """Calculate area of triangle given three points."""
    if len(points) < 3:
        return 0.0
    
    p1, p2, p3 = points[:3]
    return abs((p1[0]*(p2[1] - p3[1]) + p2[0]*(p3[1] - p1[1]) + p3[0]*(p1[1] - p2[1])) / 2.0)


def register(register_fn) -> None:
    """Register this plugin with the geometry system."""
    register_fn(PLUGIN_NAME, generate)


def _grid_fallback_tris(
    width: int, height: int, rng: random.Random, input_image=None
) -> List[Dict]:
    """Build a jittered grid and triangulate each cell in a checker pattern."""
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
            for idx, t in enumerate(tris):
                # Calculate triangle centroid for color sampling
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
                })
    return shapes


def _sample_image_color(
    input_image, x: float, y: float, canvas_width: int, canvas_height: int
) -> Tuple[int, int, int]:
    """Sample color from input image at given coordinates, with fallback to gray if no image."""
    if input_image is None:
        # Fallback to a neutral gray if no image provided
        return (128, 128, 128)

    try:
        # Get image dimensions
        img_width, img_height = input_image.size

        # Map canvas coordinates to image coordinates
        img_x = int((x / canvas_width) * img_width)
        img_y = int((y / canvas_height) * img_height)

        # Clamp coordinates to image bounds
        img_x = max(0, min(img_width - 1, img_x))
        img_y = max(0, min(img_height - 1, img_y))

        # Sample pixel color
        pixel = input_image.getpixel((img_x, img_y))

        # Handle different image modes
        if isinstance(pixel, tuple):
            if len(pixel) >= 3:
                # RGB or RGBA
                return (int(pixel[0]), int(pixel[1]), int(pixel[2]))
            elif len(pixel) == 1:
                # Grayscale
                return (int(pixel[0]), int(pixel[0]), int(pixel[0]))
        else:
            # Single value (grayscale)
            return (int(pixel), int(pixel), int(pixel))

    except Exception:
        # Fallback to gray if sampling fails
        return (128, 128, 128)

    # Default fallback
    return (128, 128, 128)


def _canonicalize_triangles(shapes: List[Dict]) -> List[Dict]:
    """Stable, cross-version order: by centroid and then by lexicographic vertex list."""
    def key(shape: Dict):
        pts = shape.get("points", [])
        # Sort triangle vertices lexicographically for a stable signature
        vs = sorted((float(x), float(y)) for x, y in pts)
        cx = round(sum(x for x, _ in vs) / 3.0, 3)
        cy = round(sum(y for _, y in vs) / 3.0, 3)
        flat = tuple(round(v, 3) for xy in vs for v in xy)
        return (cx, cy, flat)

    return sorted(shapes, key=key)


# NOTE: render() function removed to force CLI to use generate() directly
# This avoids the CLI parameter passing bug with **kwargs functions