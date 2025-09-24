# cubist_art v2.3.7 — geometry plugin: Rectangles (quadtree-ish)
# File: geometry_plugins/rectangles.py

from __future__ import annotations

import random
from typing import Dict, List, Tuple

PLUGIN_NAME = "rectangles"


def generate(
    canvas_size: Tuple[int, int],
    total_points: int = 64,
    seed: int = 0,
    **params,
) -> List[Dict]:
    """
    Note: This geometry ignores any seed_points parameter.
    """
    width, height = canvas_size
    rng = random.Random(int(seed))
    Rect = Tuple[float, float, float, float]
    rects: List[Rect] = [(0.0, 0.0, float(width), float(height))]
    target = max(4, int(total_points))
    while len(rects) < target:
        idx = max(range(len(rects)), key=lambda i: rects[i][2] * rects[i][3])
        x, y, w, h = rects.pop(idx)
        if w < 8 or h < 8:
            rects.append((x, y, w, h))
            if len(rects) >= target:
                break
            continue
        split_vertical = rng.random() < 0.5
        if split_vertical:
            cut = rng.uniform(0.33, 0.67) * w
            rects.append((x, y, cut, h))
            rects.append((x + cut, y, w - cut, h))
        else:
            cut = rng.uniform(0.33, 0.67) * h
            rects.append((x, y, w, cut))
            rects.append((x, y + cut, w, h - cut))
    shapes: List[Dict] = []
    for i, (x, y, w, h) in enumerate(rects):
        shapes.append(
            {
                "type": "polygon",
                "points": [
                    (float(x), float(y)),
                    (float(x + w), float(y)),
                    (float(x + w), float(y + h)),
                    (float(x), float(y + h)),
                ],
                "fill": (
                    (41 * (i + 1)) % 255,
                    (83 * (i + 3)) % 255,
                    (191 * (i + 5)) % 255,
                ),
                "stroke": (0, 0, 0),
                "stroke_width": 0.5,
            }
        )
    return shapes


def register(register_fn) -> None:
    register_fn(PLUGIN_NAME, generate)
