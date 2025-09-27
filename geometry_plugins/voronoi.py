# cubist_art v2.3.7 – geometry plugin: Voronoi
# File: geometry_plugins/voronoi.py

from __future__ import annotations

import random
from typing import Dict, List, Tuple, Optional

PLUGIN_NAME = "voronoi"


def generate(
    canvas_size: Tuple[int, int],
    total_points: int = 128,
    seed: int = 0,
    seed_points: Optional[List[Tuple[float, float]]] = None,
    input_image=None,
    **params,
) -> List[Dict]:
    width, height = canvas_size
    rng = random.Random(int(seed))
    if seed_points and len(seed_points) >= 3:
        pts = [tuple(map(float, pt)) for pt in seed_points]
    else:
        pts = [
            (rng.uniform(0, width), rng.uniform(0, height))
            for _ in range(max(3, int(total_points)))
        ]
    try:
        import numpy as _np
        from scipy.spatial import Voronoi as _Voronoi  # type: ignore

        v = _Voronoi(_np.array(pts, dtype=float))
        regions = _voronoi_finite_polygons_2d(v)
        shapes: List[Dict] = []
        for region, site_idx in regions:
            poly = _clip_poly_to_bbox(region, (0.0, 0.0, float(width), float(height)))
            if len(poly) >= 3:
                # Calculate polygon centroid for color sampling
                centroid_x = sum(x for x, y in poly) / len(poly)
                centroid_y = sum(y for x, y in poly) / len(poly)

                shapes.append(
                    {
                        "type": "polygon",
                        "points": [(float(x), float(y)) for x, y in poly],
                        "fill": _sample_image_color(
                            input_image, centroid_x, centroid_y, width, height
                        ),
                        "stroke": (0, 0, 0),
                        "stroke_width": 0.5,
                    }
                )
        if shapes:

            def vkey(s):
                pts = s.get("points", [])
                cx = round(sum(x for x, _ in pts) / max(1, len(pts)), 3)
                cy = round(sum(y for _, y in pts) / max(1, len(pts)), 3)
                return (cx, cy)

            shapes = sorted(shapes, key=vkey)
            return shapes
    except Exception:
        pass
    radius = max(1.0, 0.0075 * min(width, height))
    return [
        {
            "type": "circle",
            "cx": float(x),
            "cy": float(y),
            "r": float(radius),
            "fill": _sample_image_color(input_image, x, y, width, height),
            "stroke": "none",
        }
        for (x, y) in pts
    ]


def register(register_fn) -> None:
    register_fn(PLUGIN_NAME, generate)


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


def _voronoi_finite_polygons_2d(voronoi) -> List[Tuple[List[Tuple[float, float]], int]]:
    import numpy as np

    shapes = []
    center = voronoi.points.mean(axis=0)
    radius = voronoi.points.ptp().max() * 2
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
        vs = np.unique(new_vertices)
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
