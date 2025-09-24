# geometry_plugins/concentric_circles.py
# Cubism Art Project — V2.3.7 Part 2
# Purpose: Provide BOTH registry-style registration AND a default `generate()`
#          entry point for --enable-plugin-exec CLI mode.
# Notes:
#  - `generate(canvas_size, total_points, seed, **kwargs)` mirrors other plugins.
#  - Keeps the existing callable for geometry_registry: `concentric_circles(...)`.
#  - Deterministic layout; seed kept for signature compatibility.

from __future__ import annotations
from typing import List, Tuple, Optional, Sequence


def _unpack_wh(canvas_size: Sequence[int]) -> Tuple[int, int]:
    """Accept (W,H) or (W,H,C)."""
    if not isinstance(canvas_size, (tuple, list)) or len(canvas_size) < 2:
        raise ValueError("canvas_size must be a sequence like (W, H) or (W, H, C)")
    w = int(canvas_size[0])
    h = int(canvas_size[1])
    return w, h


def concentric_circles(
    canvas_size: Sequence[int],
    total_points: int = 12,
    seed: Optional[int] = None,
    **kwargs,
) -> List[Tuple[float, float, float]]:
    """
    Return `total_points` circles centered on the canvas.
    Each item is (cx, cy, r). Radii are strictly positive.
    Deterministic for given (canvas_size, total_points[, seed]).
    """
    width, height = _unpack_wh(canvas_size)
    cx = float(width) / 2.0
    cy = float(height) / 2.0

    n = max(1, int(total_points))
    max_r = 0.45 * float(min(width, height))
    if n == 1:
        radii = [max(1.0, max_r * 0.5)]
    else:
        step = max_r / float(n)
        radii = [max(1.0, (i + 1) * step) for i in range(n)]

    return [(cx, cy, float(r)) for r in radii]


# --- Default entry for --enable-plugin-exec mode ---


def generate(
    canvas_size: Sequence[int],
    total_points: int = 12,
    seed: Optional[int] = None,
    **kwargs,
):
    """CLI plugin entrypoint used by --enable-plugin-exec.
    Delegates to `concentric_circles`.
    """
    return concentric_circles(
        canvas_size, total_points=total_points, seed=seed, **kwargs
    )


# --- Registry-style optional API ---


def register(register_geometry) -> None:
    """geometry_registry.load_plugins will call this if present."""
    register_geometry("concentric_circles", concentric_circles)


# Optional mapping mode (the registry also supports this style).
GEOMETRY_MODES = {
    "concentric_circles": concentric_circles,
}
