# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: geometry_plugins/scatter_circles.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:02+02:00
# === CUBIST STAMP END ===

# =============================================================================
# Cubist Art Tool — Scatter Circles Plugin
# File: geometry_plugins/scatter_circles.py
# Version: v2.3
# Date: 2025-08-25
# Description:
#   Deterministic scatter of circles using stratified jitter grid.
#   Returns a list of (cx, cy, r) ints for color-sampled circle rendering.
# =============================================================================

import math
import random


def geometry_fn(image_shape, total_points: int, seed: int):
    # Accept (H, W) or (H, W, C)
    if len(image_shape) == 3:
        h, w, _ = image_shape
    else:
        h, w = image_shape

    n = int(total_points)
    if n < 1:
        return []

    # Stratified grid size
    grid_n = math.ceil(math.sqrt(n))
    cell_w = w / grid_n
    cell_h = h / grid_n
    prng = random.Random(seed)

    # Generate all grid cell indices
    cells = [(i, j) for i in range(grid_n) for j in range(grid_n)]
    prng.shuffle(cells)

    points = []
    for idx in range(n):
        i, j = cells[idx % len(cells)]
        # Jitter within cell
        cx = int(prng.uniform(i * cell_w, min((i + 1) * cell_w, w)))
        cy = int(prng.uniform(j * cell_h, min((j + 1) * cell_h, h)))
        # Clamp to bounds
        cx = max(0, min(w - 1, cx))
        cy = max(0, min(h - 1, cy))
        r = max(1, int(0.35 * min(cell_w, cell_h)))
        points.append((cx, cy, r))
    return points


def register(register_fn):
    register_fn("scatter_circles", geometry_fn)


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:02+02:00
# === CUBIST FOOTER STAMP END ===
