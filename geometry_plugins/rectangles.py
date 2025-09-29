# geometry_plugins/rectangles.py - Coverage-First with Bold Size Variance
# Strategy: Random placement with dramatic size range and overlap

from __future__ import annotations

import random
import math
from typing import Dict, List, Tuple, Set

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


PLUGIN_NAME = "rectangles"


def generate(
    canvas_size: Tuple[int, int],
    total_points: int = 500,
    seed: int = 0,
    input_image=None,
    min_size_multiplier: float = 0.25,  # 0.25x average - SMALLER
    max_size_multiplier: float = 5.0,  # 5.0x average - MUCH LARGER
    aspect_ratio_variance: float = 4.0,  # Increased from 3.5
    cascade_fill_enabled: bool = False,
    cascade_intensity: float = 0.8,
    overlap_tolerance: float = -3.0,
    verbose: bool = False,
    **params,
) -> List[Dict]:
    """
    Coverage-First Rectangle Algorithm with Bold Size Variance

    Enhanced size range:
    - Minimum: 0.25x average (tiny rectangles)
    - Maximum: 5.0x average (very large rectangles)
    - Creates dramatic size contrast and visual interest

    Parameters:
    - min_size_multiplier: Minimum size as fraction of average (default: 0.25)
    - max_size_multiplier: Maximum size as fraction of average (default: 5.0)
    - aspect_ratio_variance: Width/height variation (default: 4.0)
    """
    width, height = canvas_size
    rng = random.Random(int(seed))

    if verbose:
        print(
            f"[rectangles] Coverage-First with Bold Variance - Cascade: {'ENABLED' if cascade_fill_enabled else 'DISABLED'}"
        )
        print(
            f"[rectangles] Canvas: {width}x{height}, Target: {total_points} rectangles"
        )

    # Determine base count
    if cascade_fill_enabled:
        base_count = max(int(total_points * 0.6), 20)
        if verbose:
            print(
                f"[rectangles] Cascade mode: {base_count} base + {total_points - base_count} cascade"
            )
    else:
        base_count = total_points
        if verbose:
            print(f"[rectangles] Default mode: {base_count} rectangles")

    # Calculate size metrics
    canvas_area = width * height
    avg_area_per_rect = canvas_area / base_count
    avg_side_length = math.sqrt(avg_area_per_rect)

    if verbose:
        print(f"[rectangles] Average rectangle area: {avg_area_per_rect:.0f} px²")
        print(f"[rectangles] Average side length: {avg_side_length:.1f} px")
        print(
            f"[rectangles] Size range: {min_size_multiplier}x to {max_size_multiplier}x average"
        )
        print(
            f"[rectangles] Min size: ~{avg_side_length * min_size_multiplier:.1f}px, Max size: ~{avg_side_length * max_size_multiplier:.1f}px"
        )

    # Generate rectangles with bold size variance
    base_rectangles = _generate_coverage_first_rectangles(
        canvas_size,
        base_count,
        seed,
        avg_side_length,
        min_size_multiplier,
        max_size_multiplier,
        aspect_ratio_variance,
        overlap_tolerance,
        verbose,
    )

    # Convert to shape format
    base_shapes = []
    for x, y, w, h in base_rectangles:
        center_x = x + w / 2
        center_y = y + h / 2
        color = sample_image_color(input_image, center_x, center_y, width, height)

        base_shapes.append(
            {
                "type": "polygon",
                "points": [
                    (float(x), float(y)),
                    (float(x + w), float(y)),
                    (float(x + w), float(y + h)),
                    (float(x), float(y + h)),
                ],
                "fill": color,
                "stroke": "none",
                "stroke_width": 0,
            }
        )

    if verbose:
        print(f"[rectangles] Generated {len(base_shapes)} base rectangles")

    # Apply cascade fill if enabled
    final_shapes = base_shapes

    if cascade_fill_enabled and len(base_shapes) < total_points:
        if verbose:
            print("[rectangles] Applying cascade fill")

        def generate_cascade_rectangle() -> Dict:
            cascade_size = avg_side_length * cascade_intensity * 0.4
            w, h = _generate_rectangle_size(
                cascade_size * 0.5, cascade_size * 1.5, aspect_ratio_variance, rng
            )
            return {
                "type": "polygon",
                "points": [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)],
                "fill": "rgb(128,128,128)",
                "stroke": "none",
                "stroke_width": 0,
            }

        enhanced_shapes = apply_universal_cascade_fill(
            shapes=base_shapes,
            canvas_size=canvas_size,
            target_count=total_points,
            shape_generator=generate_cascade_rectangle,
            seed=seed + 1000,
            verbose=verbose,
        )

        # Update colors
        cascade_shapes = enhanced_shapes[len(base_shapes) :]
        for shape in cascade_shapes:
            if shape.get("type") == "polygon" and "points" in shape:
                points = shape["points"]
                centroid_x = sum(p[0] for p in points) / len(points)
                centroid_y = sum(p[1] for p in points) / len(points)
                shape["fill"] = sample_image_color(
                    input_image, centroid_x, centroid_y, width, height
                )

        final_shapes = enhanced_shapes

        if verbose:
            print(f"[rectangles] Cascade fill added {len(cascade_shapes)} rectangles")

    # Calculate statistics
    if verbose:
        total_area = sum(
            _calculate_polygon_area(shape["points"])
            for shape in final_shapes
            if shape.get("type") == "polygon" and "points" in shape
        )
        coverage = (total_area / canvas_area) * 100
        print(f"[rectangles] Final count: {len(final_shapes)} rectangles")
        print(f"[rectangles] Total area coverage: {coverage:.1f}% (includes overlaps)")
        print(
            f"[rectangles] Mode: {'CASCADE FILL' if cascade_fill_enabled else 'DEFAULT'}"
        )

    return final_shapes


def _generate_coverage_first_rectangles(
    canvas_size: Tuple[int, int],
    count: int,
    seed: int,
    avg_side_length: float,
    min_mult: float,
    max_mult: float,
    aspect_variance: float,
    overlap_tolerance: float,
    verbose: bool = False,
) -> List[Tuple[float, float, float, float]]:
    """
    Generate rectangles with bold size variance and coverage-first placement.
    """
    width, height = canvas_size
    rng = random.Random(seed)

    placed_rects: List[Tuple[float, float, float, float]] = []
    spatial_grid = SpatialGrid(width, height, grid_size=64)

    max_attempts_per_rect = 100
    consecutive_failures = 0
    max_consecutive_failures = 20

    # Use power-law distribution for size to favor variety
    # More small rectangles, fewer large ones, dramatic range
    for i in range(count):
        placed = False

        for attempt in range(max_attempts_per_rect):
            # Power-law distribution: bias toward smaller, but allow large ones
            # Use exponential distribution skewed toward lower end
            rand_val = rng.random()
            if rand_val < 0.7:
                # 70%: Small to medium (0.25x to 1.5x)
                size_multiplier = rng.uniform(min_mult, 1.5)
            elif rand_val < 0.9:
                # 20%: Medium to large (1.5x to 3.0x)
                size_multiplier = rng.uniform(1.5, 3.0)
            else:
                # 10%: Very large (3.0x to 5.0x)
                size_multiplier = rng.uniform(3.0, max_mult)

            base_size = avg_side_length * size_multiplier

            w, h = _generate_rectangle_size(
                base_size * 0.7, base_size * 1.3, aspect_variance, rng
            )

            # Random placement with center bias
            if rng.random() < 0.6:
                # Center-biased
                center_x = width / 2
                center_y = height / 2
                spread = min(width, height) * 0.4
                x = rng.gauss(center_x, spread) - w / 2
                y = rng.gauss(center_y, spread) - h / 2
            else:
                # Fully random
                x = rng.uniform(-w * 0.3, width - w * 0.7)
                y = rng.uniform(-h * 0.3, height - h * 0.7)

            # Clamp to canvas (allow some overflow for large rectangles)
            x = max(-w * 0.2, min(width - w * 0.8, x))
            y = max(-h * 0.2, min(height - h * 0.8, y))

            candidate_rect = (x, y, w, h)

            # Relaxed collision check
            if i < 5 or not spatial_grid.has_collision(
                candidate_rect, overlap_tolerance
            ):
                placed_rects.append(candidate_rect)
                spatial_grid.add_rectangle(candidate_rect)
                placed = True
                consecutive_failures = 0
                break

        if not placed:
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                if verbose:
                    print(f"[rectangles] Stopping at {len(placed_rects)} rectangles")
                break

    if verbose:
        # Calculate size distribution
        sizes = [w * h for _, _, w, h in placed_rects]
        sizes.sort()
        print(
            f"[rectangles] Size distribution: min={sizes[0]:.0f}px², median={sizes[len(sizes)//2]:.0f}px², max={sizes[-1]:.0f}px²"
        )

    return placed_rects


def _generate_rectangle_size(
    min_size: float, max_size: float, aspect_variance: float, rng: random.Random
) -> Tuple[float, float]:
    """Generate width and height with bold aspect ratio variance."""
    # Independent base sizes
    base_w = rng.uniform(min_size, max_size)
    base_h = rng.uniform(min_size, max_size)

    # Bold aspect ratio variance
    aspect_ratio = rng.uniform(1.0 / aspect_variance, aspect_variance)

    # Mix strategies with more independence
    if rng.random() < 0.5:
        # Aspect-based
        avg = (base_w + base_h) / 2
        if rng.random() < 0.5:
            w = avg * math.sqrt(aspect_ratio)
            h = avg / math.sqrt(aspect_ratio)
        else:
            w = avg / math.sqrt(aspect_ratio)
            h = avg * math.sqrt(aspect_ratio)
    else:
        # More independent sizing with wider variance
        w = base_w * rng.uniform(0.5, 1.5)
        h = base_h * rng.uniform(0.5, 1.5)

        # Clamp only extreme aspect ratios
        if w / h > aspect_variance:
            h = w / aspect_variance
        elif h / w > aspect_variance:
            w = h / aspect_variance

    return (w, h)


class SpatialGrid:
    """Coarse spatial grid for minimal collision detection."""

    def __init__(self, width: int, height: int, grid_size: int = 64):
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.cols = max(1, width // grid_size)
        self.rows = max(1, height // grid_size)
        self.cell_width = width / self.cols
        self.cell_height = height / self.rows

        self.grid: List[List[Set[int]]] = [
            [set() for _ in range(self.cols)] for _ in range(self.rows)
        ]
        self.rectangles: List[Tuple[float, float, float, float]] = []

    def add_rectangle(self, rect: Tuple[float, float, float, float]) -> int:
        rect_idx = len(self.rectangles)
        self.rectangles.append(rect)

        x, y, w, h = rect
        start_col = max(0, int(x // self.cell_width))
        end_col = min(self.cols - 1, int((x + w) // self.cell_width))
        start_row = max(0, int(y // self.cell_height))
        end_row = min(self.rows - 1, int((y + h) // self.cell_height))

        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                self.grid[row][col].add(rect_idx)

        return rect_idx

    def has_collision(
        self, test_rect: Tuple[float, float, float, float], tolerance: float = 0.0
    ) -> bool:
        """Returns True only if rectangle is substantially overlapping (>80% area)."""
        x, y, w, h = test_rect

        start_col = max(0, int(x // self.cell_width))
        end_col = min(self.cols - 1, int((x + w) // self.cell_width))
        start_row = max(0, int(y // self.cell_height))
        end_row = min(self.rows - 1, int((y + h) // self.cell_height))

        checked_rects: Set[int] = set()

        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                for rect_idx in self.grid[row][col]:
                    if rect_idx in checked_rects:
                        continue
                    checked_rects.add(rect_idx)

                    existing_rect = self.rectangles[rect_idx]
                    if _rectangles_substantially_overlap(
                        test_rect, existing_rect, tolerance
                    ):
                        return True

        return False


def _rectangles_substantially_overlap(
    rect1: Tuple[float, float, float, float],
    rect2: Tuple[float, float, float, float],
    tolerance: float = 0.0,
) -> bool:
    """Check if rectangles overlap by more than 80%."""
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2

    # Calculate overlap region
    overlap_x1 = max(x1, x2)
    overlap_y1 = max(y1, y2)
    overlap_x2 = min(x1 + w1, x2 + w2)
    overlap_y2 = min(y1 + h1, y2 + h2)

    # No overlap
    if overlap_x1 >= overlap_x2 - tolerance or overlap_y1 >= overlap_y2 - tolerance:
        return False

    # Calculate overlap area
    overlap_width = overlap_x2 - overlap_x1
    overlap_height = overlap_y2 - overlap_y1
    overlap_area = overlap_width * overlap_height

    # Calculate smaller rectangle area
    area1 = w1 * h1
    area2 = w2 * h2
    smaller_area = min(area1, area2)

    # Reject only if overlap is >80% of smaller rectangle
    return overlap_area > (smaller_area * 0.8)


def _calculate_polygon_area(points: List[Tuple[float, float]]) -> float:
    """Calculate area using shoelace formula."""
    if len(points) < 3:
        return 0.0

    area = 0.0
    for i in range(len(points)):
        j = (i + 1) % len(points)
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]

    return abs(area) / 2.0


def register(register_fn) -> None:
    """Register this plugin with the geometry system."""
    register_fn(PLUGIN_NAME, generate)
