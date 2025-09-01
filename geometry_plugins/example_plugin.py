# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: geometry_plugins/example_plugin.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:02+02:00
# === CUBIST STAMP END ===

# === FILE: geometry_plugins/example_plugin.py ===
# === UPDATED: 2025-08-22T14:45:00Z ===
"""
Example geometry plugin for Cubist Art Tool.

Defines a minimal deterministic triangle scatterer named "toy_triangles".
"""

import numpy as np


def toy_triangles(image_shape, total_points=10, seed=None, **kwargs):
    """
    Generate a list of triangles (as 3-point tuples) scattered over the image.
    Deterministic if seed is provided.
    Always returns at least one triangle if total_points >= 3.
    """
    h, w = image_shape[:2]
    n = max(3, int(total_points))
    rng = np.random.default_rng(seed)
    pts = rng.uniform([0, 0], [w, h], size=(n, 2))
    tris = []
    # Ensure at least one triangle is returned if possible
    for i in range(0, n - n % 3, 3):
        tris.append(tuple(map(tuple, pts[i : i + 3])))
    # If not enough for a full triangle, pad with the first points
    if n % 3 != 0 and n >= 3:
        last = tuple(map(tuple, pts[-3:]))
        tris.append(last)
    return tris


GEOMETRY_MODES = {"toy_triangles": toy_triangles}

# === EOF geometry_plugins/example_plugin.py @ 2025-08-22T14:45:00Z ===


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:02+02:00
# === CUBIST FOOTER STAMP END ===
