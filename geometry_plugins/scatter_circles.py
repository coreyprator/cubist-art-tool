# geometry_plugins/scatter_circles.py - Enhanced with Universal Cascade Fill
# Scatter circles with grid-jitter blue-noise, sized to resemble the source
#
# API: compatible with cubist_cli plugin loader
#   - generate(canvas_size: (W,H), total_points:int=1000, seed:int=0, **params)
#   - register(register_geometry) -> None

from __future__ import annotations

import math
import random
from typing import Callable, Iterable, List, Sequence, Tuple, Dict

# Import universal cascade fill system
try:
    from cascade_fill_system import apply_universal_cascade_fill, sample_image_color
except ImportError:
    # Fallback if cascade system not available
    def apply_universal_cascade_fill(
        shapes, canvas_size, target_count, shape_generator, seed=42, verbose=False
    ):
        return shapes

    def sample_image_color(input_image, x, y, canvas_width, canvas_height):
        return "rgb(128,128,128)"

# ---- trace helpers (robust to different import styles) -----------------------
try:  # try package-relative first
    from ._trace import TRACE, t, dump, try_stats  # type: ignore
except Exception:
    try:
        from geometry_plugins._trace import TRACE, t, dump, try_stats  # type: ignore
    except Exception:  # final fallback: no-ops
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


def _auto_radius(W: int, H: int, total_points: int, min_dist_factor: float = 0.008) -> float:
    """Calculate radius based on canvas size and spacing, following universal formula."""
    total_points = max(1, int(total_points))
    
    # Use universal formula: dense packing with overlapping circles for complete coverage
    diagonal = math.sqrt(W * W + H * H)
    min_dist = diagonal * min_dist_factor
    
    # For complete coverage with no white space: radius = min_dist * 1.0 (overlapping)
    radius = min_dist * 1.0
    
    # Ensure reasonable minimum radius
    radius = max(radius, 3.0)
    
    return radius


def _grid_jitter_samples(
    W: int, H: int, total_points: int, rng: random.Random, margin: float, min_dist_factor: float = 0.008
) -> List[Tuple[float, float]]:
    """Evenly scatter ~total_points samples over the canvas via grid jitter.

    Enhanced with dense packing parameters for better coverage.
    """
    total_points = max(1, int(total_points))
    
    # FIXED: Use smaller cell size for denser packing (following universal formula)
    diagonal = math.sqrt(W * W + H * H)
    min_dist = diagonal * min_dist_factor
    s = min_dist  # Use minimum distance as cell size for dense packing
    
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
    min_dist_factor: float = 0.008,  # FIXED: Use dense packing default
    **kwargs,
) -> List[dict]:
    """Return a list of circles as dict format for SVG export.

    Enhanced with dense packing and universal spacing formula for better coverage.
    """
    W, H = _unpack_wh(canvas_size)
    rng = random.Random(int(seed))

    # Compute radius using universal formula
    if radius in (None, "auto"):
        r = _auto_radius(W, H, total_points, min_dist_factor)
    else:
        r = float(radius)
        if r <= 0:
            r = _auto_radius(W, H, total_points, min_dist_factor)

    # Edge margin so circles stay on-canvas
    if margin == "auto":
        m = r
    else:
        m = float(margin)
        if m < 0:
            m = 0.0

    if TRACE:
        t(
            f"canvas={W}x{H} total_points={total_points} seed={seed} radius={r:.4f} jitter={jitter} min_dist_factor={min_dist_factor}"
        )

    # Build jittered grid samples across the full extent with dense packing
    pts = _grid_jitter_samples(W, H, total_points, rng, margin=m, min_dist_factor=min_dist_factor)

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

    # Convert to dict format for SVG export
    circle_data = []
    for x, y, radius in circles:
        circle_dict = {
            "type": "circle",
            "cx": float(x),
            "cy": float(y),
            "r": float(radius),
            "fill": _sample_image_color(input_image, x, y, W, H),
            "stroke": "none",  # Remove strokes for cleaner look
            "stroke_width": 0,
        }
        circle_data.append(circle_dict)

    return circle_data


def generate(
    canvas_size: Sequence[int],
    total_points: int = 1000,
    seed: int = 0,
    input_image=None,
    min_dist_factor: float = None,  # Auto-calculate if None
    cascade_fill_enabled: bool = False,
    cascade_intensity: float = 0.8,
    verbose: bool = False,
    **kwargs,
) -> List[dict]:
    """Generate scattered circles and return shapes for SVG export.

    Args:
        canvas_size: (width, height) tuple
        total_points: Maximum number of points to generate
        seed: Random seed for reproducibility
        input_image: PIL Image object for color sampling
        min_dist_factor: Minimum distance factor (auto-calculated if None)
        cascade_fill_enabled: Enable cascade fill (default: False)
        cascade_intensity: Cascade fill intensity (default: 0.8)
        verbose: Enable debug logging
        **kwargs: Additional parameters

    Returns:
        List of circle dictionaries with 'type', 'cx', 'cy', 'r' keys
    """
    W, H = canvas_size
    
    if verbose:
        print(
            f"[scatter_circles] Scatter circles generation - Cascade: {'ENABLED' if cascade_fill_enabled else 'DISABLED'}"
        )
        print(
            f"[scatter_circles] Canvas: {W}x{H}, Target: {total_points} points"
        )

    # Adjust target for cascade mode
    if cascade_fill_enabled:
        base_target = max(int(total_points * 0.7), 20)  # Generate 70% base points for cascade fill
        if verbose:
            print(
                f"[scatter_circles] Cascade mode: generating {base_target} base points, then cascade fill"
            )
    else:
        base_target = total_points
        if verbose:
            print(f"[scatter_circles] Default mode: generating {base_target} points")

    # FIXED: Use dense packing for better coverage
    if min_dist_factor is None:
        min_dist_factor = 0.008  # Dense packing for more points
        if verbose:
            print(
                f"[scatter_circles] Using ultra-dense packing min_dist_factor: {min_dist_factor}"
            )
    else:
        if verbose:
            print(f"[scatter_circles] Using provided min_dist_factor: {min_dist_factor}")

    # Get the base circles using enhanced algorithm
    try:
        shapes = scatter_circles(
            canvas_size, 
            base_target, 
            seed, 
            input_image=input_image,
            min_dist_factor=min_dist_factor,
            verbose=verbose,
            **kwargs
        )
        if verbose:
            print(f"[scatter_circles] Generated {len(shapes)} scatter circle shapes")
    except Exception as e:
        if verbose:
            print(f"[scatter_circles] Error in scatter_circles: {e}")
        # Fallback to simple circles if algorithm fails
        random.seed(seed)
        shapes = []
        radius = _auto_radius(W, H, base_target, min_dist_factor)
        for _ in range(base_target):
            x = random.uniform(radius, W - radius)
            y = random.uniform(radius, H - radius)
            shapes.append({
                "type": "circle",
                "cx": float(x),
                "cy": float(y),
                "r": float(radius),
                "fill": _sample_image_color(input_image, x, y, W, H),
                "stroke": "none",
                "stroke_width": 0,
            })

    if verbose:
        print(f"[scatter_circles] Generated {len(shapes)} base circles")

    # Apply cascade fill if enabled
    if cascade_fill_enabled and len(shapes) < total_points:
        if verbose:
            print("[scatter_circles] Applying cascade fill")

        # Get base radius from first shape for cascade sizing
        base_radius = shapes[0]["r"] if shapes else _auto_radius(W, H, total_points, min_dist_factor)
        cascade_radius = base_radius * cascade_intensity * 0.4

        def generate_cascade_circle() -> Dict:
            radius = random.uniform(cascade_radius * 0.6, cascade_radius * 1.2)
            return {
                "type": "circle",
                "cx": 0.0,  # Will be positioned by cascade system
                "cy": 0.0,
                "r": float(radius),
                "fill": "rgb(128,128,128)",  # Placeholder
                "stroke": "none",
                "stroke_width": 0,
            }

        # Apply universal cascade fill
        enhanced_shapes = apply_universal_cascade_fill(
            shapes=shapes,
            canvas_size=canvas_size,
            target_count=total_points,
            shape_generator=generate_cascade_circle,
            seed=seed + 1000,
            verbose=verbose,
        )

        # Update colors for cascade shapes
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


# Registry support (used when not in plugin-exec mode)
def register(register_geometry: Callable[[str, Callable[..., Iterable]], None]) -> None:
    register_geometry("scatter_circles", generate)


def _sample_image_color(
    input_image, x: float, y: float, canvas_width: int, canvas_height: int
) -> str:
    """Sample color from input image at given coordinates, with fallback to gray if no image.
    
    FIXED: Returns RGB string format like 'rgb(r,g,b)' to match other geometries.
    """
    if input_image is None:
        # Fallback to a neutral gray if no image provided
        return "rgb(128,128,128)"

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
                return f"rgb({int(pixel[0])},{int(pixel[1])},{int(pixel[2])})"
            elif len(pixel) == 1:
                # Grayscale
                return f"rgb({int(pixel[0])},{int(pixel[0])},{int(pixel[0])})"
        else:
            # Single value (grayscale)
            return f"rgb({int(pixel)},{int(pixel)},{int(pixel)})"

    except Exception:
        # Fallback to gray if sampling fails
        return "rgb(128,128,128)"

    # Default fallback
    return "rgb(128,128,128)"


PLUGIN_NAME = "scatter_circles"

GEOMETRY_MODES = {
    "scatter_circles": generate,
}