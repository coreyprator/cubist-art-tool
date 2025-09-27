# cubist_art v2.3.7 – geometry plugin: Rectangles (quadtree-ish)
# File: geometry_plugins/rectangles.py

from __future__ import annotations

import random
from typing import Dict, List, Tuple

PLUGIN_NAME = "rectangles"


def generate(
    canvas_size: Tuple[int, int],
    total_points: int = 64,
    seed: int = 0,
    input_image=None,
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

    # FIXED: Add safety limits to prevent infinite loops
    max_iterations = target * 3  # Safety limit
    min_size = max(4.0, min(width, height) / 200)  # Dynamic minimum size
    iteration_count = 0

    while len(rects) < target and iteration_count < max_iterations:
        iteration_count += 1

        # Find largest rectangle that can still be split
        splitnable_rects = [
            (i, r) for i, r in enumerate(rects) if r[2] > min_size and r[3] > min_size
        ]

        if not splitnable_rects:
            # No more rectangles can be split - add random small ones to reach target
            remaining = target - len(rects)
            for _ in range(remaining):
                # Add small random rectangles
                x = rng.uniform(0, width - min_size)
                y = rng.uniform(0, height - min_size)
                w = rng.uniform(min_size, min(min_size * 2, width - x))
                h = rng.uniform(min_size, min(min_size * 2, height - y))
                rects.append((x, y, w, h))
            break

        # Pick the largest splittable rectangle
        idx, (x, y, w, h) = max(
            splitnable_rects, key=lambda item: item[1][2] * item[1][3]
        )
        rects.pop(idx)

        # Split the rectangle
        split_vertical = rng.random() < 0.5
        if split_vertical and w > min_size * 2:
            cut = rng.uniform(0.33, 0.67) * w
            rects.append((x, y, cut, h))
            rects.append((x + cut, y, w - cut, h))
        elif not split_vertical and h > min_size * 2:
            cut = rng.uniform(0.33, 0.67) * h
            rects.append((x, y, w, cut))
            rects.append((x, y + cut, w, h - cut))
        else:
            # Can't split this rectangle effectively, put it back
            rects.append((x, y, w, h))

        # FIXED: Break if we're not making progress
        if iteration_count > 100 and len(rects) == len(set(rects)):
            # If we've tried 100 times and all rects are unique, we're likely stuck
            break

    shapes: List[Dict] = []
    for i, (x, y, w, h) in enumerate(rects):
        # Calculate rectangle center for color sampling
        center_x = x + w / 2
        center_y = y + h / 2

        shapes.append(
            {
                "type": "polygon",
                "points": [
                    (float(x), float(y)),
                    (float(x + w), float(y)),
                    (float(x + w), float(y + h)),
                    (float(x), float(y + h)),
                ],
                "fill": _sample_image_color(
                    input_image, center_x, center_y, width, height
                ),
                "stroke": (0, 0, 0),
                "stroke_width": 0.5,
            }
        )
    return shapes


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
