# geometry_plugins/poisson_disk.py - Parameter Registry Integration
# Enhanced with configurable radius_multiplier, cascade_intensity, and opacity

from __future__ import annotations
import math
import random
from typing import List, Tuple, Dict

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
            "min_dist_factor": 0.025,
            "radius_multiplier": 1.0,
            "cascade_intensity": 0.8,
            "opacity": 0.7
        }
        return defaults.get(param)
    
    def validate_parameter(geometry, param, value):
        return True, value, ""


PLUGIN_NAME = "poisson_disk"


def poisson_disk_sampling(
    canvas_size: Tuple[int, int],
    total_points: int = 1000,
    seed: int = 0,
    min_dist_factor: float = 0.025,
    k: int = 30,
    verbose: bool = False,
    **kwargs,
) -> List[Tuple[float, float]]:
    """Generate Poisson disk sampling (blue noise)."""
    width, height = canvas_size
    random.seed(seed)

    diagonal = math.sqrt(width * width + height * height)
    min_dist = diagonal * min_dist_factor

    if verbose:
        print("[poisson_disk] Algorithm parameters:")
        print(f"  Canvas: {width}x{height}, diagonal: {diagonal:.1f}")
        print(f"  min_dist_factor: {min_dist_factor}, min_dist: {min_dist:.1f}")
        print(f"  k attempts: {k}, target points: {total_points}")

    cell_size = min_dist / math.sqrt(2)
    grid_width = int(math.ceil(width / cell_size))
    grid_height = int(math.ceil(height / cell_size))

    if verbose:
        print(f"  Grid: {grid_width}x{grid_height} cells, cell_size: {cell_size:.1f}")

    grid = [None] * (grid_width * grid_height)

    def get_cell_idx(x: float, y: float) -> int:
        cell_x = int(x / cell_size)
        cell_y = int(y / cell_size)
        idx = (
            cell_x + cell_y * grid_width
            if 0 <= cell_x < grid_width and 0 <= cell_y < grid_height
            else -1
        )
        if verbose and len(points) < 5:
            print(
                f"    get_cell_idx({x:.1f},{y:.1f}) -> cell({cell_x},{cell_y}) -> idx:{idx}"
            )
        return idx

    def get_neighbors(x: float, y: float) -> List[Tuple[float, float]]:
        neighbors = []
        cell_x = int(x / cell_size)
        cell_y = int(y / cell_size)

        for i in range(max(0, cell_x - 2), min(grid_width, cell_x + 3)):
            for j in range(max(0, cell_y - 2), min(grid_height, cell_y + 3)):
                idx = i + j * grid_width
                if 0 <= idx < len(grid) and grid[idx] is not None:
                    neighbors.append(grid[idx])

        if verbose and len(points) < 5:
            print(
                f"    get_neighbors({x:.1f},{y:.1f}) found {len(neighbors)} neighbors"
            )
        return neighbors

    def is_valid(x: float, y: float) -> bool:
        if not (0 <= x < width and 0 <= y < height):
            if verbose and len(points) < 5:
                print(f"    is_valid({x:.1f},{y:.1f}) -> FALSE (out of bounds)")
            return False

        cell_idx = get_cell_idx(x, y)
        if cell_idx == -1:
            if verbose and len(points) < 5:
                print(f"    is_valid({x:.1f},{y:.1f}) -> FALSE (invalid cell)")
            return False

        neighbors = get_neighbors(x, y)
        for nx, ny in neighbors:
            dx = x - nx
            dy = y - ny
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < min_dist:
                if verbose and len(points) < 5:
                    print(
                        f"    is_valid({x:.1f},{y:.1f}) -> FALSE (too close to {nx:.1f},{ny:.1f}, dist:{dist:.1f} < {min_dist:.1f})"
                    )
                return False

        if verbose and len(points) < 5:
            print(f"    is_valid({x:.1f},{y:.1f}) -> TRUE")
        return True

    active_points: List[Tuple[float, float]] = []
    points: List[Tuple[float, float]] = []

    first_x = random.uniform(0, width)
    first_y = random.uniform(0, height)
    active_points.append((first_x, first_y))
    points.append((first_x, first_y))

    cell_idx = get_cell_idx(first_x, first_y)
    if cell_idx >= 0:
        grid[cell_idx] = (first_x, first_y)

    if verbose:
        print(f"  Initial point: ({first_x:.1f},{first_y:.1f}) at cell {cell_idx}")

    iteration = 0
    max_iterations = total_points * k * 2

    while active_points and len(points) < total_points and iteration < max_iterations:
        iteration += 1
        idx = random.randint(0, len(active_points) - 1)
        x, y = active_points[idx]

        if verbose and iteration <= 10:
            print(
                f"  Iteration {iteration}: trying from active point {idx} at ({x:.1f},{y:.1f})"
            )

        found = False
        for attempt in range(k):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(min_dist, 2 * min_dist)
            new_x = x + radius * math.cos(angle)
            new_y = y + radius * math.sin(angle)

            if verbose and iteration <= 5 and attempt < 3:
                print(
                    f"    Attempt {attempt}: ({new_x:.1f},{new_y:.1f}) radius:{radius:.1f} angle:{angle:.2f}"
                )

            if is_valid(new_x, new_y):
                active_points.append((new_x, new_y))
                points.append((new_x, new_y))

                cell_idx = get_cell_idx(new_x, new_y)
                if cell_idx >= 0:
                    grid[cell_idx] = (new_x, new_y)

                found = True

                if verbose and iteration <= 10:
                    print(
                        f"    SUCCESS: Added point {len(points)} at ({new_x:.1f},{new_y:.1f})"
                    )

                if len(points) >= total_points:
                    break

        if not found:
            removed_point = active_points.pop(idx)
            if verbose and iteration <= 10:
                print(
                    f"    Removed exhausted active point ({removed_point[0]:.1f},{removed_point[1]:.1f})"
                )

        if verbose and iteration % 100 == 0:
            print(
                f"  Progress: {len(points)} points, {len(active_points)} active, iteration {iteration}"
            )

    if verbose:
        print("[poisson_disk] Algorithm completed:")
        print(f"  Final: {len(points)} points in {iteration} iterations")
        print(f"  Active points remaining: {len(active_points)}")
        print(
            f"  Termination reason: {'target reached' if len(points) >= total_points else 'no active points' if not active_points else 'iteration limit'}"
        )

    return points


def generate(
    canvas_size,
    total_points=1000,
    seed=0,
    input_image=None,
    min_dist_factor=None,
    radius_multiplier=None,
    cascade_fill_enabled=False,
    cascade_intensity=None,
    opacity=None,
    verbose=False,
    **kwargs,
):
    """Generate Poisson disk sampling and return shapes for SVG export."""
    
    # Apply defaults from parameter registry
    if min_dist_factor is None:
        min_dist_factor = get_parameter_default("poisson_disk", "min_dist_factor")
    else:
        # Validate and clamp
        valid, clamped, msg = validate_parameter("poisson_disk", "min_dist_factor", min_dist_factor)
        if not valid and verbose:
            print(f"[poisson_disk] Parameter validation: {msg}, using {clamped}")
        min_dist_factor = clamped
    
    if radius_multiplier is None:
        radius_multiplier = get_parameter_default("poisson_disk", "radius_multiplier")
    else:
        valid, clamped, msg = validate_parameter("poisson_disk", "radius_multiplier", radius_multiplier)
        if not valid and verbose:
            print(f"[poisson_disk] Parameter validation: {msg}, using {clamped}")
        radius_multiplier = clamped
    
    if cascade_intensity is None:
        cascade_intensity = get_parameter_default("poisson_disk", "cascade_intensity")
    else:
        valid, clamped, msg = validate_parameter("poisson_disk", "cascade_intensity", cascade_intensity)
        if not valid and verbose:
            print(f"[poisson_disk] Parameter validation: {msg}, using {clamped}")
        cascade_intensity = clamped
    
    if opacity is None:
        opacity = get_parameter_default("poisson_disk", "opacity")
    else:
        valid, clamped, msg = validate_parameter("poisson_disk", "opacity", opacity)
        if not valid and verbose:
            print(f"[poisson_disk] Parameter validation: {msg}, using {clamped}")
        opacity = clamped
    
    if verbose:
        print(
            f"[poisson_disk] Poisson disk generation - Cascade: {'ENABLED' if cascade_fill_enabled else 'DISABLED'}"
        )
        print(
            f"[poisson_disk] Canvas: {canvas_size[0]}x{canvas_size[1]}, Target: {total_points} points"
        )
        print(f"[poisson_disk] Parameters: min_dist_factor={min_dist_factor}, radius_multiplier={radius_multiplier}")
        print(f"[poisson_disk] Parameters: cascade_intensity={cascade_intensity}, opacity={opacity}")

    if cascade_fill_enabled:
        base_target = max(int(total_points * 0.7), 20)
        if verbose:
            print(
                f"[poisson_disk] Cascade mode: generating {base_target} base points, then cascade fill"
            )
    else:
        base_target = total_points
        if verbose:
            print(f"[poisson_disk] Default mode: generating {base_target} points")

    try:
        points = poisson_disk_sampling(
            canvas_size, base_target, seed, min_dist_factor, verbose=verbose, **kwargs
        )
        if verbose:
            print(f"[poisson_disk] Generated {len(points)} Poisson disk points")
    except Exception as e:
        if verbose:
            print(f"[poisson_disk] Error in poisson_disk_sampling: {e}")
        random.seed(seed)
        points = []
        width, height = canvas_size
        for _ in range(base_target):
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            points.append((x, y))

    width, height = canvas_size
    diagonal = math.sqrt(width * width + height * height)
    min_dist = diagonal * min_dist_factor
    
    # Apply radius_multiplier to control coverage
    point_radius = min_dist * radius_multiplier
    point_radius = max(point_radius, 3.0)

    if verbose:
        print(f"[poisson_disk] Min distance: {min_dist:.1f} pixels")
        print(
            f"[poisson_disk] Circle radius: {point_radius:.1f} pixels (multiplier: {radius_multiplier})"
        )

    # Convert points to circle shapes with INTEGER coordinates
    shapes = []
    for x, y in points:
        shapes.append(
            {
                "type": "circle",
                "cx": int(round(x)),
                "cy": int(round(y)),
                "r": int(round(point_radius)),
                "fill": _sample_image_color(input_image, x, y, width, height),
                "stroke": "none",
                "stroke_width": 0,
                "opacity": opacity,  # Pass opacity to shape
            }
        )

    if verbose:
        print(f"[poisson_disk] Generated {len(shapes)} base circles")

    if cascade_fill_enabled and len(shapes) < total_points:
        if verbose:
            print("[poisson_disk] Applying cascade fill")

        cascade_radius = point_radius * cascade_intensity * 0.4

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
                color = _sample_image_color(input_image, cx, cy, width, height)
                shape["fill"] = color

        shapes = enhanced_shapes

        if verbose:
            print(f"[poisson_disk] Cascade fill added {len(cascade_shapes)} circles")

    if verbose:
        print(f"[poisson_disk] Final count: {len(shapes)} circles")
        print(
            f"[poisson_disk] Mode: {'CASCADE FILL' if cascade_fill_enabled else 'DEFAULT'}"
        )

    return shapes


def register(register_fn) -> None:
    """Register this plugin with the geometry system."""
    register_fn(PLUGIN_NAME, generate)


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