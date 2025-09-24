# cubist_art v2.3.7 — geometry plugin: Delaunay
# File: geometry_plugins/delaunay.py

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple, Optional

PLUGIN_NAME = "delaunay"


def generate(
    canvas_size: Tuple[int, int],
    total_points: int = 256,
    seed: int = 0,
    seed_points: Optional[List[Tuple[float, float]]] = None,
    **params,
) -> List[Dict]:
    width, height = canvas_size
    rng = random.Random(int(seed))

    # Use provided seeds if available, otherwise sample uniformly
    if seed_points and len(seed_points) >= 3:
        pts = [tuple(map(float, pt)) for pt in seed_points]
    else:
        n = max(3, int(total_points))
        pts = [(rng.uniform(0, width), rng.uniform(0, height)) for _ in range(n)]

    # Prefer SciPy Delaunay; otherwise use a jittered grid fallback
    try:
        import numpy as _np
        from scipy.spatial import Delaunay as _Delaunay  # type: ignore

        tri = _Delaunay(_np.array(pts, dtype=float))
        shapes: List[Dict] = []
        for simplex in tri.simplices:
            p0 = tuple(map(float, tri.points[simplex[0]]))
            p1 = tuple(map(float, tri.points[simplex[1]]))
            p2 = tuple(map(float, tri.points[simplex[2]]))
            shapes.append(
                {
                    "type": "polygon",
                    "points": [p0, p1, p2],
                    "fill": _stable_color(int(simplex[0])),
                    "stroke": (0, 0, 0),
                    "stroke_width": 0.5,
                }
            )
        return _canonicalize_triangles(shapes)
    except Exception:
        shapes = _grid_fallback_tris(width, height, rng)
        return _canonicalize_triangles(shapes)


def register(register_fn) -> None:
    register_fn(PLUGIN_NAME, generate)


def _grid_fallback_tris(width: int, height: int, rng: random.Random) -> List[Dict]:
    # Build a jittered grid and triangulate each cell in a checker pattern
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
                shapes.append(
                    {
                        "type": "polygon",
                        "points": [
                            (float(t[0][0]), float(t[0][1])),
                            (float(t[1][0]), float(t[1][1])),
                            (float(t[2][0]), float(t[2][1])),
                        ],
                        "fill": _stable_color(i + j + idx),
                        "stroke": (0, 0, 0),
                        "stroke_width": 0.5,
                    }
                )
    return shapes


def _stable_color(k: int) -> Tuple[int, int, int]:
    return (
        (53 * (k + 1)) % 255,
        (97 * (k + 3)) % 255,
        (149 * (k + 7)) % 255,
    )


def _canonicalize_triangles(shapes: List[Dict]) -> List[Dict]:
    # Stable, cross-version order: by centroid and then by lexicographic vertex list
    def key(shape: Dict):
        pts = shape.get("points", [])
        # Sort triangle vertices lexicographically for a stable signature
        vs = sorted((float(x), float(y)) for x, y in pts)
        cx = round(sum(x for x, _ in vs) / 3.0, 3)
        cy = round(sum(y for _, y in vs) / 3.0, 3)
        flat = tuple(round(v, 3) for xy in vs for v in xy)
        return (cx, cy, flat)

    return sorted(shapes, key=key)
