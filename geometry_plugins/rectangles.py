# geometry_plugins/rectangles.py - Fixed CLI Compatibility
# Remove render() wrapper to force CLI to use generate() directly

from __future__ import annotations

import random
import math
from typing import Dict, List, Tuple, Optional, Set

# Import universal cascade fill system
try:
    from cascade_fill_system import apply_universal_cascade_fill, sample_image_color
except ImportError:
    # Fallback if cascade system not available
    def apply_universal_cascade_fill(shapes, canvas_size, target_count, shape_generator, seed=42, verbose=False):
        return shapes
    def sample_image_color(input_image, x, y, canvas_width, canvas_height):
        return "rgb(128,128,128)"

PLUGIN_NAME = "rectangles"


def generate(
    canvas_size: Tuple[int, int],
    total_points: int = 500,  # CHANGED: Default 500 instead of 64
    seed: int = 0,
    input_image=None,
    min_size_factor: float = 0.3,
    max_size_factor: float = 1.5,
    aspect_ratio_variance: float = 2.0,
    cascade_fill_enabled: bool = False,
    cascade_intensity: float = 0.8,
    max_placement_attempts: int = 100,
    adjacency_tolerance: float = 1.0,
    verbose: bool = False,
    **params,
) -> List[Dict]:
    """
    Enhanced Rectangle Algorithm with Universal Cascade Fill Integration
    
    Parameters:
    - cascade_fill_enabled: Enable universal cascade fill system (default: False for backward compatibility)
    - cascade_intensity: How aggressively to fill gaps (0.0-1.0, default: 0.8)
    - min_size_factor: Minimum rectangle size as factor of standard deviation (default 0.3)
    - max_size_factor: Maximum rectangle size as factor of standard deviation (default 1.5)  
    - aspect_ratio_variance: Width/height can vary by this factor (default 2.0)
    - max_placement_attempts: Maximum attempts to place each rectangle (default 100)
    - adjacency_tolerance: Pixel tolerance for adjacent placement (default 1.0)
    """
    width, height = canvas_size
    rng = random.Random(int(seed))
    
    if verbose:
        print(f"[rectangles] Rectangle generation - Cascade: {'ENABLED' if cascade_fill_enabled else 'DISABLED'}")
        print(f"[rectangles] Canvas: {width}x{height}, Target: {total_points} rectangles")
    
    # Phase 1: Generate base rectangles (60-70% of target if cascade enabled)
    if cascade_fill_enabled:
        base_count = max(int(total_points * 0.6), 20)  # 60% for base when cascade enabled
        if verbose:
            print(f"[rectangles] Cascade mode: generating {base_count} base rectangles, {total_points - base_count} cascade")
    else:
        base_count = total_points  # All rectangles in default mode
        if verbose:
            print(f"[rectangles] Default mode: generating {base_count} rectangles")
    
    # Calculate size metrics
    canvas_area = width * height
    avg_area_per_rect = canvas_area / base_count
    base_size = math.sqrt(avg_area_per_rect)
    
    min_size = max(2.0, base_size * min_size_factor)
    max_size = min(min(width, height) * 0.3, base_size * max_size_factor)
    
    if verbose:
        print(f"[rectangles] Size range: {min_size:.1f} - {max_size:.1f} pixels")
    
    # Generate base rectangles using existing algorithm
    base_rectangles = _generate_base_rectangles(
        canvas_size, base_count, seed, min_size, max_size, 
        aspect_ratio_variance, max_placement_attempts, adjacency_tolerance, verbose
    )
    
    # Convert base rectangles to shape format
    base_shapes = []
    for i, (x, y, w, h) in enumerate(base_rectangles):
        center_x = x + w / 2
        center_y = y + h / 2
        
        color = sample_image_color(input_image, center_x, center_y, width, height)
        
        base_shapes.append({
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
        })
    
    if verbose:
        print(f"[rectangles] Generated {len(base_shapes)} base rectangles")
    
    # Phase 2: Apply cascade fill if enabled
    final_shapes = base_shapes
    
    if cascade_fill_enabled and len(base_shapes) < total_points:
        if verbose:
            print(f"[rectangles] Applying universal cascade fill (intensity: {cascade_intensity})")
        
        # Create shape generator for cascade rectangles
        def generate_cascade_rectangle() -> Dict:
            # Generate smaller rectangles for gap filling
            cascade_base_size = base_size * cascade_intensity * 0.5
            w, h = _generate_rectangle_size(
                cascade_base_size * 0.3, 
                cascade_base_size * 0.8, 
                aspect_ratio_variance, 
                rng
            )
            
            # Return rectangle at origin - cascade system will position it
            return {
                "type": "polygon",
                "points": [
                    (0.0, 0.0),
                    (w, 0.0),
                    (w, h),
                    (0.0, h),
                ],
                "fill": "rgb(128,128,128)",  # Placeholder color
                "stroke": "none",
                "stroke_width": 0,
            }
        
        # Apply universal cascade fill
        enhanced_shapes = apply_universal_cascade_fill(
            shapes=base_shapes,
            canvas_size=canvas_size,
            target_count=total_points,
            shape_generator=generate_cascade_rectangle,
            seed=seed + 1000,  # Different seed for cascade
            verbose=verbose
        )
        
        # Update colors for cascade shapes based on their final positions
        cascade_shapes = enhanced_shapes[len(base_shapes):]
        for shape in cascade_shapes:
            if shape.get("type") == "polygon" and "points" in shape:
                points = shape["points"]
                # Calculate centroid
                centroid_x = sum(p[0] for p in points) / len(points)
                centroid_y = sum(p[1] for p in points) / len(points)
                # Sample color at final position
                shape["fill"] = sample_image_color(input_image, centroid_x, centroid_y, width, height)
        
        final_shapes = enhanced_shapes
        
        if verbose:
            print(f"[rectangles] Universal cascade fill added {len(cascade_shapes)} rectangles")
    
    # Calculate final statistics
    if verbose:
        total_area = sum(
            _calculate_polygon_area(shape["points"]) 
            for shape in final_shapes 
            if shape.get("type") == "polygon" and "points" in shape
        )
        canvas_area = width * height
        coverage = (total_area / canvas_area) * 100
        
        print(f"[rectangles] Final count: {len(final_shapes)} rectangles")
        print(f"[rectangles] Canvas coverage: {coverage:.1f}%")
        print(f"[rectangles] Mode: {'CASCADE FILL' if cascade_fill_enabled else 'DEFAULT'}")
    
    return final_shapes


def _generate_base_rectangles(
    canvas_size: Tuple[int, int],
    count: int,
    seed: int,
    min_size: float,
    max_size: float,
    aspect_variance: float,
    max_attempts: int,
    tolerance: float,
    verbose: bool = False
) -> List[Tuple[float, float, float, float]]:
    """Generate base rectangles using existing adjacent fit algorithm."""
    width, height = canvas_size
    rng = random.Random(seed)
    
    placed_rects: List[Tuple[float, float, float, float]] = []
    spatial_grid = SpatialGrid(width, height, grid_size=max(16, int(max_size * 0.5)))
    
    # Place initial seed rectangles
    initial_count = min(4, count // 20)
    if verbose:
        print(f"[rectangles] Placing {initial_count} initial seed rectangles")
    
    for seed_idx in range(initial_count):
        # Distribute initial rectangles across canvas regions
        if seed_idx == 0:
            region_x, region_y = width * 0.3, height * 0.3
            region_w, region_h = width * 0.4, height * 0.4
        elif seed_idx == 1:
            region_x, region_y = 0, 0
            region_w, region_h = width * 0.6, height * 0.6
        elif seed_idx == 2:
            region_x, region_y = width * 0.4, height * 0.4
            region_w, region_h = width * 0.6, height * 0.6
        else:
            region_x, region_y = 0, 0
            region_w, region_h = width, height
        
        w, h = _generate_rectangle_size(min_size, max_size, aspect_variance, rng)
        x = rng.uniform(region_x, max(region_x, region_x + region_w - w))
        y = rng.uniform(region_y, max(region_y, region_y + region_h - h))
        
        x = max(0, min(width - w, x))
        y = max(0, min(height - h, y))
        
        initial_rect = (x, y, w, h)
        placed_rects.append(initial_rect)
        spatial_grid.add_rectangle(initial_rect)
    
    # Place remaining rectangles using mixed strategy
    failed_placements = 0
    for i in range(initial_count, count):
        use_random = (i % 5 == 0) or (len(placed_rects) < 10)
        
        if use_random:
            rect = _place_random_rectangle(
                spatial_grid, width, height, min_size, max_size,
                aspect_variance, rng, max_attempts, tolerance
            )
        else:
            rect = _place_adjacent_rectangle(
                placed_rects, spatial_grid, width, height, min_size, max_size, 
                aspect_variance, rng, max_attempts, tolerance
            )
        
        if rect is not None:
            placed_rects.append(rect)
            spatial_grid.add_rectangle(rect)
        else:
            failed_placements += 1
            
        if failed_placements > count * 0.2:
            break
    
    if verbose:
        print(f"[rectangles] Base algorithm placed {len(placed_rects)} rectangles")
    
    return placed_rects


def _generate_rectangle_size(
    min_size: float, 
    max_size: float, 
    aspect_variance: float, 
    rng: random.Random
) -> Tuple[float, float]:
    """Generate width and height with proper aspect ratio variation."""
    base = rng.uniform(min_size, max_size)
    aspect_ratio = rng.uniform(1.0 / aspect_variance, aspect_variance)
    
    if rng.random() < 0.5:
        w = base * math.sqrt(aspect_ratio)
        h = base / math.sqrt(aspect_ratio)
    else:
        w = base / math.sqrt(aspect_ratio)
        h = base * math.sqrt(aspect_ratio)
    
    return (w, h)


def _place_random_rectangle(
    spatial_grid: 'SpatialGrid',
    canvas_width: int,
    canvas_height: int,
    min_size: float,
    max_size: float,
    aspect_variance: float,
    rng: random.Random,
    max_attempts: int,
    tolerance: float
) -> Optional[Tuple[float, float, float, float]]:
    """Place a rectangle at a random position."""
    for attempt in range(max_attempts):
        w, h = _generate_rectangle_size(min_size, max_size, aspect_variance, rng)
        
        if attempt < max_attempts // 3:
            x = rng.uniform(0, canvas_width - w)
            y = rng.uniform(0, canvas_height - h)
        else:
            # Edge-biased placement
            edge_margin = min(w, h) * 2
            if rng.random() < 0.5:
                if rng.random() < 0.5:
                    x = rng.uniform(0, edge_margin)
                else:
                    x = rng.uniform(canvas_width - w - edge_margin, canvas_width - w)
                y = rng.uniform(0, canvas_height - h)
            else:
                x = rng.uniform(0, canvas_width - w)
                if rng.random() < 0.5:
                    y = rng.uniform(0, edge_margin)
                else:
                    y = rng.uniform(canvas_height - h - edge_margin, canvas_height - h)
        
        x = max(0, min(canvas_width - w, x))
        y = max(0, min(canvas_height - h, y))
        
        candidate_rect = (x, y, w, h)
        
        if not spatial_grid.has_collision(candidate_rect, tolerance):
            return candidate_rect
    
    return None


def _place_adjacent_rectangle(
    existing_rects: List[Tuple[float, float, float, float]],
    spatial_grid: 'SpatialGrid',
    canvas_width: int,
    canvas_height: int,
    min_size: float,
    max_size: float,
    aspect_variance: float,
    rng: random.Random,
    max_attempts: int,
    tolerance: float
) -> Optional[Tuple[float, float, float, float]]:
    """Find a valid adjacent position for a new rectangle."""
    for attempt in range(max_attempts):
        w, h = _generate_rectangle_size(min_size, max_size, aspect_variance, rng)
        
        target_rect = rng.choice(existing_rects)
        tx, ty, tw, th = target_rect
        
        candidate_positions = [
            (tx + tw + tolerance, ty + rng.uniform(-h * 0.7, th - h * 0.3)),
            (tx + tw + tolerance, ty + rng.uniform(-h * 0.3, th - h * 0.7)),
            (tx - w - tolerance, ty + rng.uniform(-h * 0.7, th - h * 0.3)),
            (tx - w - tolerance, ty + rng.uniform(-h * 0.3, th - h * 0.7)),
            (tx + rng.uniform(-w * 0.7, tw - w * 0.3), ty + th + tolerance),
            (tx + rng.uniform(-w * 0.3, tw - w * 0.7), ty + th + tolerance),
            (tx + rng.uniform(-w * 0.7, tw - w * 0.3), ty - h - tolerance),
            (tx + rng.uniform(-w * 0.3, tw - w * 0.7), ty - h - tolerance),
        ]
        
        for x, y in candidate_positions:
            margin = 1.0
            if x < -margin or y < -margin or x + w > canvas_width + margin or y + h > canvas_height + margin:
                continue
                
            x = max(0, min(canvas_width - w, x))
            y = max(0, min(canvas_height - h, y))
            
            candidate_rect = (x, y, w, h)
            
            if not spatial_grid.has_collision(candidate_rect, tolerance * 0.5):
                return candidate_rect
    
    return None


class SpatialGrid:
    """Spatial grid for efficient collision detection."""
    
    def __init__(self, width: int, height: int, grid_size: int = 32):
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
        """Add rectangle to spatial grid and return its index."""
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
        self, 
        test_rect: Tuple[float, float, float, float], 
        tolerance: float = 0.0
    ) -> bool:
        """Check if test rectangle collides with any existing rectangles."""
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
                    if _rectangles_overlap(test_rect, existing_rect, tolerance):
                        return True
        
        return False


def _rectangles_overlap(
    rect1: Tuple[float, float, float, float],
    rect2: Tuple[float, float, float, float],
    tolerance: float = 0.0
) -> bool:
    """Check if two rectangles overlap."""
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    
    return not (
        x1 + w1 <= x2 - tolerance or
        x2 + w2 <= x1 - tolerance or
        y1 + h1 <= y2 - tolerance or
        y2 + h2 <= y1 - tolerance
    )


def _calculate_polygon_area(points: List[Tuple[float, float]]) -> float:
    """Calculate area of polygon using shoelace formula."""
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

# NOTE: render() function removed to force CLI to use generate() directly
# This avoids the CLI parameter passing bug with **kwargs functions