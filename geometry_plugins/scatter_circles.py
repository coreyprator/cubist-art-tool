# geometry_plugins/scatter_circles.py
# Scatter circles with grid–jitter blue–noise, sized to resemble the source
#
# API: compatible with cubist_cli plugin loader
#   - generate(canvas_size: (W,H), total_points:int=1000, seed:int=0, **params)
#   - register(register_geometry) -> None
#
# Notes
# -----
# • We purposely avoid importing relatively ("from ._trace …") because the
#   loader may import this module without a package context. We fall back to
#   lightweight no–ops if tracing helpers are unavailable.
# • Radius is computed to roughly match the visual scale of Poisson–disk output
#   for the same point budget: r ≈ 0.55 * sqrt((W*H)/N). This makes the scatter
#   result look more like the input when fills are sampled downstream.

from __future__ import annotations

import math
import random
from typing import Callable, Iterable, List, Sequence, Tuple

# ---- trace helpers (robust to different import styles) -----------------------
try:  # try package–relative first
    from ._trace import TRACE, t, dump, try_stats  # type: ignore
except Exception:
    try:
        from geometry_plugins._trace import TRACE, t, dump, try_stats  # type: ignore
    except Exception:  # final fallback: no–ops
        TRACE = False  # type: ignore

        def t(msg: str) -> None:  # type: ignore
            pass

        def dump(label: str, data) -> None:  # type: ignore
            pass

        def try_stats(samples):  # type: ignore
            return {
                "n": len(samples) if hasattr(samples, "__len__") else 0,
            }


# ---- core helpers ------------------------------------------------------------


def _unpack_wh(canvas_size: Sequence[int]) -> Tuple[int, int]:
    if not isinstance(canvas_size, (tuple, list)) or len(canvas_size) < 2:
        raise ValueError("canvas_size must be a sequence like (W, H) or (W, H, C)")
    W = int(canvas_size[0])
    H = int(canvas_size[1])
    if W <= 0 or H <= 0:
        raise ValueError("canvas_size must be positive (W, H)")
    return W, H


def _auto_radius(W: int, H: int, total_points: int) -> float:
    total_points = max(1, int(total_points))
    # Heuristic chosen to roughly match the perceptual scale of Poisson output
    # at the same point budget (empirically ~0.55 keeps the look comparable).
    return 0.55 * math.sqrt((W * H) / float(total_points))


def _grid_jitter_samples(
    W: int, H: int, total_points: int, rng: random.Random, margin: float
) -> List[Tuple[float, float]]:
    """Evenly scatter ~total_points samples over the canvas via grid jitter.

    We build a grid with cell size s ≈ sqrt((W*H)/N) and pick one random point
    per cell. If that yields more than N samples, we downsample. If fewer, we
    add uniform random points to reach N.
    """
    total_points = max(1, int(total_points))
    s = math.sqrt((W * H) / float(total_points))
    cols = max(1, int(round(W / s)))
    rows = max(1, int(round(H / s)))
    pts: List[Tuple[float, float]] = []
    for j in range(rows):
        for i in range(cols):
            x0 = i * s
            y0 = j * s
            x = x0 + rng.random() * s
            y = y0 + rng.random() * s
            # clamp to keep a margin so circles don't clip the edges
            if margin > 0:
                x = min(max(x, margin), W - margin)
                y = min(max(y, margin), H - margin)
            pts.append((x, y))
    # Balance count to requested total_points
    if len(pts) > total_points:
        # downsample deterministically with PRNG for reproducibility
        rng.shuffle(pts)
        pts = pts[:total_points]
    elif len(pts) < total_points:
        need = total_points - len(pts)
        for _ in range(need):
            x = rng.random() * W
            y = rng.random() * H
            if margin > 0:
                x = min(max(x, margin), W - margin)
                y = min(max(y, margin), H - margin)
            pts.append((x, y))
    return pts


# ---- public plugin API -------------------------------------------------------


def scatter_circles(
    canvas_size: Sequence[int],
    total_points: int = 1000,
    seed: int = 0,
    *,
    radius: float | str | None = "auto",
    jitter: float = 0.25,
    margin: float | str = "auto",
    input_image=None,
    **kwargs,
) -> List[dict]:  # Changed return type annotation
    """Return a list of circles as (x, y, r).

    The pipeline will sample colors from the source image at (x, y) and fill
    the circles accordingly, so using a radius comparable to Poisson's output
    helps the result resemble the input.
    """
    W, H = _unpack_wh(canvas_size)
    rng = random.Random(int(seed))

    # Compute radius
    if radius in (None, "auto"):
        r = _auto_radius(W, H, total_points)
    else:
        r = float(radius)
        if r <= 0:
            r = _auto_radius(W, H, total_points)

    # Edge margin so circles stay on–canvas
    if margin == "auto":
        m = r
    else:
        m = float(margin)
        if m < 0:
            m = 0.0

    if TRACE:
        t(
            f"canvas={W}x{H} total_points={total_points} seed={seed} radius={r:.4f} jitter={jitter}"
        )

    # Build jittered grid samples across the full extent
    pts = _grid_jitter_samples(W, H, total_points, rng, margin=m)

    # Apply small random jitter relative to radius to avoid lattice look
    if jitter and jitter > 0:
        J = float(jitter)
        J_abs = J * r
        pts = [
            (
                min(max(x + (rng.random() * 2 - 1) * J_abs, m), W - m),
                min(max(y + (rng.random() * 2 - 1) * J_abs, m), H - m),
            )
            for (x, y) in pts
        ]

    circles = [(x, y, r) for (x, y) in pts]

    if TRACE:
        # lightweight stats for debugging
        try:
            xs = [c[0] for c in circles]
            ys = [c[1] for c in circles]
            dump(
                "samples",
                {
                    "n": len(circles),
                    "xmin": min(xs) if xs else None,
                    "xmax": max(xs) if xs else None,
                    "ymin": min(ys) if ys else None,
                    "ymax": max(ys) if ys else None,
                    "r": r,
                },
            )
        except Exception:
            pass

    # Convert to dict format for SVG export (moved this to the end)
    circle_data = []
    for x, y, radius in circles:
        circle_dict = {
            "type": "circle",
            "cx": float(x),
            "cy": float(y),
            "r": float(radius),
            "fill": _sample_image_color(input_image, x, y, W, H),
            "stroke": "none",
        }
        circle_data.append(circle_dict)

    return circle_data  # Return dict format, not tuples


# Default entry point for --enable-plugin-exec


def generate(
    canvas_size: Sequence[int],
    total_points: int = 1000,
    seed: int = 0,
    input_image=None,
    **kwargs,
) -> List[dict]:  # Changed return type annotation
    # Call scatter_circles which now returns dict format
    return scatter_circles(
        canvas_size,
        total_points=total_points,
        seed=seed,
        input_image=input_image,
        **kwargs,
    )


# Registry support (used when not in plugin–exec mode)


def register(register_geometry: Callable[[str, Callable[..., Iterable]], None]) -> None:
    register_geometry("scatter_circles", scatter_circles)


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


GEOMETRY_MODES = {
    "scatter_circles": scatter_circles,
}
