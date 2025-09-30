# geometry_plugins/scatter_circles.py - Parameter Registry Integration
# Enhanced with configurable radius_multiplier, jitter, cascade_intensity, and opacity

from __future__ import annotations

import math
import random
from typing import Callable, Iterable, List, Sequence, Tuple, Dict

# Import universal cascade fill system
try:
    from cascade_fill_system import apply_universal_cascade_fill, sample_image_color
except ImportError:
    def apply_universal_cascade_fill(
        shapes, canvas_size, target_count, shape_generator, seed=42, verbose=False
    ):
        return shapes

    def sample_image_color(input_image, x, y, canvas_width, canvas_height):
        return "rgb(128,128,128)"

# Import parameter registry
try:
    from geometry_parameters import get_parameter_default, validate_parameter
except ImportError:
    def get_parameter_default(geometry, param):
        defaults = {
            "min_dist_factor": 0.008,
            "radius_multiplier": 1.0,
            "jitter": 0.25,
            "cascade_intensity": 0.8,
            "opacity": 0.7
        }
        return defaults.get(param)
    
    def validate_parameter(geometry, param, value):
        return True, value, ""


# ---- trace helpers (robust to different import styles) -----------------------
try:
    from ._trace import TRACE, t, dump, try_stats
except Exception:
    try:
        from geometry_plugins._trace import TRACE, t, dump, try_stats
    except Exception:
        TRACE = False

        def t(msg: str) -> None:
            pass

        def dump(label: str, data) -> None:
            pass

        def try_stats(samples):
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


def _auto_radius(
    W: int, H: int, total_points: int, min_dist_factor: float = 0.008, radius_multiplier: float = 1.0
) -> float:
    """Calculate radius based on canvas size, spacing, and coverage multiplier."""
    total_points = max(1, int(total_points))

    # Use universal formula: spacing determines base distance
    diagonal = math.sqrt(W * W + H * H)
    min_dist = diagonal * min_dist_factor

    # Apply radius multiplier for coverage control
    radius = min_dist * radius_multiplier

    # Ensure reasonable minimum radius
    radius = max(radius, 3.0)

    return radius


def _grid_jitter_samples(
    W: int,
    H: int,
    total_points: int,
    rng: random.Random,
    margin: float,
    min_dist_factor: float = 0.008,
) -> List[Tuple[float, float]]:
    """Evenly scatter ~total_points samples over the canvas via grid jitter."""
    total_points = max(1, int(total_points))

    # Use minimum distance as cell size for dense packing
    diagonal = math.sqrt(W * W + H * H)
    min_dist = diagonal * min_dist_factor
    s = min_dist

    cols = max(1, int(round(W / s)))
    rows = max(1, int(round(H / s)))
    pts: List[Tuple[float, float]] = []

    for j in range(rows):
        for i in range(cols):
            x0 = i * s
            y0 = j * s
            x = x0 + rng.random() * s
            y = y0 + rng.random() * s
            if margin > 0:
                x = min(max(x, margin), W - margin)
                y = min(max(y, margin), H - margin)
            pts.append((x, y))

    # Balance count to requested total_points
    if len(pts) > total_points:
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
    min_dist_factor: float = 0.008,
    radius_multiplier: float = 1.0,
    opacity: float = 0.7,
    **kwargs,
) -> List[dict]:
    """Return a list of circles as dict format for SVG export."""
    W, H = _unpack_wh(canvas_size)
    rng = random.Random(int(seed))

    if radius in (None, "auto"):
        r = _auto_radius(W, H, total_points, min_dist_factor, radius_multiplier)
    else:
        r = float(radius)
        if r <= 0:
            r = _auto_radius(W, H, total_points, min_dist_factor, radius_multiplier)

    if margin == "auto":
        m = r
    else:
        m = float(margin)
        if m < 0:
            m = 0.0

    if TRACE:
        t(
            f"canvas={W}x{H} total_points={total_points} seed={seed} radius={r:.4f} jitter={jitter} min_dist_factor={min_dist_factor} radius_multiplier={radius_multiplier}"
        )

    pts = _grid_jitter_samples(
        W, H, total_points, rng, margin=m, min_dist_factor=min_dist_factor
    )

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

    # Convert to dict format with INTEGER coordinates
    circle_data = []
    for x, y, radius in circles:
        circle_dict = {
            "type": "circle",
            "cx": int(round(x)),
            "cy": int(round(y)),
            "r": int(round(radius)),
            "fill": _sample_image_color(input_image, x, y, W, H),
            "stroke": "none",
            "stroke_width": 0,
            "opacity": opacity,  # Pass opacity to shape
        }
        circle_data.append(circle_dict)

    return circle_data


def generate(
    canvas_size: Sequence[int],
    total_points: int = 1000,
    seed: int = 0,
    input_image=None,
    min_dist_factor: float = None,
    radius_multiplier: float = None,
    jitter: float = None,
    cascade_fill_enabled: bool = False,
    cascade_intensity: float = None,
    opacity: float = None,
    verbose: bool = False,
    **kwargs,
) -> List[dict]:
    """Generate scattered circles and return shapes for SVG export."""
    W, H = canvas_size

    # Apply defaults from parameter registry
    if min_dist_factor is None:
        min_dist_factor = get_parameter_default("scatter_circles", "min_dist_factor")
    else:
        valid, clamped, msg = validate_parameter("scatter_circles", "min_dist_factor", min_dist_factor)
        if not valid and verbose:
            print(f"[scatter_circles] Parameter validation: {msg}, using {clamped}")
        min_dist_factor = clamped
    
    if radius_multiplier is None:
        radius_multiplier = get_parameter_default("scatter_circles", "radius_multiplier")
    else:
        valid, clamped, msg = validate_parameter("scatter_circles", "radius_multiplier", radius_multiplier)
        if not valid and verbose:
            print(f"[scatter_circles] Parameter validation: {msg}, using {clamped}")
        radius_multiplier = clamped
    
    if jitter is None:
        jitter = get_parameter_default("scatter_circles", "jitter")
    else:
        valid, clamped, msg = validate_parameter("scatter_circles", "jitter", jitter)
        if not valid and verbose:
            print(f"[scatter_circles] Parameter validation: {msg}, using {clamped}")
        jitter = clamped
    
    if cascade_intensity is None:
        cascade_intensity = get_parameter_default("scatter_circles", "cascade_intensity")
    else:
        valid, clamped, msg = validate_parameter("scatter_circles", "cascade_intensity", cascade_intensity)
        if not valid and verbose:
            print(f"[scatter_circles] Parameter validation: {msg}, using {clamped}")
        cascade_intensity = clamped
    
    if opacity is None:
        opacity = get_parameter_default("scatter_circles", "opacity")
    else:
        valid, clamped, msg = validate_parameter("scatter_circles", "opacity", opacity)
        if not valid and verbose:
            print(f"[scatter_circles] Parameter validation: {msg}, using {clamped}")
        opacity = clamped

    if verbose:
        print(
            f"[scatter_circles] Scatter circles generation - Cascade: {'ENABLED' if cascade_fill_enabled else 'DISABLED'}"
        )
        print(f"[scatter_circles] Canvas: {W}x{H}, Target: {total_points} points")
        print(f"[scatter_circles] Parameters: min_dist_factor={min_dist_factor}, radius_multiplier={radius_multiplier}")
        print(f"[scatter_circles] Parameters: jitter={jitter}, cascade_intensity={cascade_intensity}, opacity={opacity}")

    if cascade_fill_enabled:
        base_target = max(int(total_points * 0.7), 20)
        if verbose:
            print(
                f"[scatter_circles] Cascade mode: generating {base_target} base points, then cascade fill"
            )
    else:
        base_target = total_points
        if verbose:
            print(f"[scatter_circles] Default mode: generating {base_target} points")

    try:
        shapes = scatter_circles(
            canvas_size,
            base_target,
            seed,
            input_image=input_image,
            min_dist_factor=min_dist_factor,
            radius_multiplier=radius_multiplier,
            jitter=jitter,
            opacity=opacity,
            verbose=verbose,
            **kwargs,
        )
        if verbose:
            print(f"[scatter_circles] Generated {len(shapes)} scatter circle shapes")
    except Exception as e:
        if verbose:
            print(f"[scatter_circles] Error in scatter_circles: {e}")
        random.seed(seed)
        shapes = []
        radius = _auto_radius(W, H, base_target, min_dist_factor, radius_multiplier)
        for _ in range(base_target):
            x = random.uniform(radius, W - radius)
            y = random.uniform(radius, H - radius)
            shapes.append(
                {
                    "type": "circle",
                    "cx": int(round(x)),
                    "cy": int(round(y)),
                    "r": int(round(radius)),
                    "fill": _sample_image_color(input_image, x, y, W, H),
                    "stroke": "none",
                    "stroke_width": 0,
                    "opacity": opacity,
                }
            )

    if verbose:
        print(f"[scatter_circles] Generated {len(shapes)} base circles")

    if cascade_fill_enabled and len(shapes) < total_points:
        if verbose:
            print("[scatter_circles] Applying cascade fill")

        base_radius = (
            shapes[0]["r"]
            if shapes
            else _auto_radius(W, H, total_points, min_dist_factor, radius_multiplier)
        )
        cascade_radius = base_radius * cascade_intensity * 0.4

        def generate_cascade_circle() -> Dict:
            radius = random.uniform(cascade_radius * 0.6, cascade_radius * 1.2)
            return {
                "type": "circle",
                "cx": 0,
                "cy": 0,
                "r": int(round(radius)),
                "fill": "rgb(128,128,128)",
                "stroke": "none",
                "stroke_width": 0,
                "opacity": opacity,  # Pass opacity to cascade shapes too
            }

        enhanced_shapes = apply_universal_cascade_fill(
            shapes=shapes,
            canvas_size=canvas_size,
            target_count=total_points,
            shape_generator=generate_cascade_circle,
            seed=seed + 1000,
            verbose=verbose,
        )

        cascade_shapes = enhanced_shapes[len(shapes) :]
        for shape in cascade_shapes:
            if shape.get("type") == "circle":
                cx = shape.get("cx", 0)
                cy = shape.get("cy", 0)
                color = _sample_image_color(input_image, cx, cy, W, H)
                shape["fill"] = color

        shapes = enhanced_shapes

        if verbose:
            print(f"[scatter_circles] Cascade fill added {len(cascade_shapes)} circles")

    if verbose:
        print(f"[scatter_circles] Final count: {len(shapes)} circles")
        print(
            f"[scatter_circles] Mode: {'CASCADE FILL' if cascade_fill_enabled else 'DEFAULT'}"
        )

    return shapes


# Registry support
def register(register_geometry: Callable[[str, Callable[..., Iterable]], None]) -> None:
    register_geometry("scatter_circles", generate)


def _sample_image_color(
    input_image, x: float, y: float, canvas_width: int, canvas_height: int
) -> str:
    """Sample color from input image at given coordinates."""
    if input_image is None:
        return "rgb(128,128,128)"

    try:
        img_width, img_height = input_image.size
        img_x = int((x / canvas_width) * img_width)
        img_y = int((y / canvas_height) * img_height)
        img_x = max(0, min(img_width - 1, img_x))
        img_y = max(0, min(img_height - 1, img_y))
        pixel = input_image.getpixel((img_x, img_y))

        if isinstance(pixel, tuple):
            if len(pixel) >= 3:
                return f"rgb({int(pixel[0])},{int(pixel[1])},{int(pixel[2])})"
            elif len(pixel) == 1:
                return f"rgb({int(pixel[0])},{int(pixel[0])},{int(pixel[0])})"
        else:
            return f"rgb({int(pixel)},{int(pixel)},{int(pixel)})"

    except Exception:
        return "rgb(128,128,128)"

    return "rgb(128,128,128)"


PLUGIN_NAME = "scatter_circles"

GEOMETRY_MODES = {
    "scatter_circles": generate,
}