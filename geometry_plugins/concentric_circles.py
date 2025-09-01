# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: geometry_plugins/concentric_circles.py
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:34+02:00
# === CUBIST STAMP END ===

# ============================================================================
# Cubist Art Tool — Concentric Circles Plugin
# File: geometry_plugins/concentric_circles.py
# Version: v2.3-fixB
# Date: 2025-09-01
# Summary:
#   Deterministic generator returning a list of (cx, cy, r) tuples centered
#   on the canvas. Accepts canvas_size as (W,H) or (W,H,C).
#   Radii are strictly positive. Seed is accepted but not required.
# ============================================================================

from __future__ import annotations

from typing import List, Tuple, Optional, Sequence


def _unpack_wh(canvas_size: Sequence[int]) -> Tuple[int, int]:
    """
    Accept (W, H) or (W, H, C). Ignore any trailing channels dimension.
    """
    if not isinstance(canvas_size, (tuple, list)) or len(canvas_size) < 2:
        raise ValueError("canvas_size must be a sequence like (W, H) or (W, H, C)")
    w = int(canvas_size[0])
    h = int(canvas_size[1])
    return w, h


def concentric_circles(
    canvas_size: Sequence[int],
    total_points: int = 12,
    seed: Optional[int] = None,  # kept for signature compatibility/determinism
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

    # Ensure a sane count and radius ladder within canvas
    n = max(1, int(total_points))
    max_r = 0.45 * float(min(width, height))
    if n == 1:
        radii = [max(1.0, max_r * 0.5)]
    else:
        step = max_r / float(n)
        radii = [max(1.0, (i + 1) * step) for i in range(n)]

    # Deterministic ordering — no need to use RNG; honoring seed param is optional.
    return [(cx, cy, float(r)) for r in radii]


def register(register_geometry) -> None:
    """geometry_registry.load_plugins will call this if present."""
    register_geometry("concentric_circles", concentric_circles)


# Optional mapping mode (the registry also supports this style).
GEOMETRY_MODES = {
    "concentric_circles": concentric_circles,
}


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:34+02:00
# === CUBIST FOOTER STAMP END ===
