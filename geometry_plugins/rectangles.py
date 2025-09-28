# cubist_art v2.5.0 – geometry plugin: Rectangles (Adjacent Fit - Fixed)
# File: geometry_plugins/rectangles.py

from __future__ import annotations

import random
import math
from typing import Dict, List, Tuple, Optional, Set

PLUGIN_NAME = "rectangles"


def generate(
    canvas_size: Tuple[int, int],
    total_points: int = 64,
    seed: int = 0,
    input_image=None,
    min_size_factor: float = 0.3,
    max_size_factor: float = 1.5,
    aspect_ratio_variance: float = 2.0,
    cascade_fill_enabled: bool = True,
    max_placement_attempts: int = 100,
    adjacency_tolerance: float = 1.0,
    verbose: bool = False,
    **params,
) -> List[Dict]:
    """
    Adjacent Fit Rectangle Algorithm - Fixed Version
    
    Parameters:
    - min_size_factor: Minimum rectangle size as factor of standard deviation (default 0.3)
    - max_size_factor: Maximum rectangle size as factor of standard deviation (default 1.5)  
    - aspect_ratio_variance: Width/height can vary by this factor (default 2.0)
    - cascade_fill_enabled: Fill gaps with smaller rectangles (default True)
    - max_placement_attempts: Maximum attempts to place each rectangle (default 100)
    - adjacency_tolerance: Pixel tolerance for adjacent placement (default 1.0)
    """
    width, height = canvas_size
    rng = random.Random(int(seed))
    
    # Calculate size metrics - more aggressive sizing
    canvas_area = width * height
    target_count = max(4, int(total_points))
    avg_area_per_rect = canvas_area / target_count
    base_size = math.sqrt(avg_area_per_rect)
    
    # Tighter size constraints for better packing
    min_size = max(2.0, base_size * min_size_factor)
    max_size = min(min(width, height) * 0.3, base_size * max_size_factor)
    
    if verbose:
        print(f"[rectangles] Target: {target_count} rectangles")
        print(f"[rectangles] Canvas: {width}x{height} = {canvas_area:,} pixels")
        print(f"[rectangles] Size range: {min_size:.1f} - {max_size:.1f} pixels")
        print(f"[rectangles] Expected area per rectangle: {avg_area_per_rect:.0f} pixels")
    
    # Storage for placed rectangles
    placed_rects: List[Tuple[float, float, float, float]] = []  # (x, y, w, h)
    spatial_grid = SpatialGrid(width, height, grid_size=max(16, int(max_size * 0.5)))
    
    # Statistics tracking
    failed_placements = 0
    total_attempts = 0
    
    # Place initial rectangles with better distribution
    initial_count = min(4, target_count // 20)  # Start with multiple seed rectangles
    if verbose:
        print(f"[rectangles] Placing {initial_count} initial seed rectangles")
    
    for seed_idx in range(initial_count):
        # Distribute initial rectangles across canvas regions
        if seed_idx == 0:
            # Center region
            region_x = width * 0.3
            region_y = height * 0.3
            region_w = width * 0.4
            region_h = height * 0.4
        elif seed_idx == 1:
            # Top-left region
            region_x = 0
            region_y = 0
            region_w = width * 0.6
            region_h = height * 0.6
        elif seed_idx == 2:
            # Bottom-right region
            region_x = width * 0.4
            region_y = height * 0.4
            region_w = width * 0.6
            region_h = height * 0.6
        else:
            # Random region
            region_x = 0
            region_y = 0
            region_w = width
            region_h = height
        
        w, h = _generate_rectangle_size(min_size, max_size, aspect_ratio_variance, rng)
        x = rng.uniform(region_x, max(region_x, region_x + region_w - w))
        y = rng.uniform(region_y, max(region_y, region_y + region_h - h))
        
        # Ensure within canvas bounds
        x = max(0, min(width - w, x))
        y = max(0, min(height - h, y))
        
        initial_rect = (x, y, w, h)
        placed_rects.append(initial_rect)
        spatial_grid.add_rectangle(initial_rect)
        
        if verbose:
            print(f"[rectangles] Seed #{seed_idx}: {w:.1f}x{h:.1f} at ({x:.1f},{y:.1f})")
    
    # Place remaining rectangles using mixed strategy
    for i in range(initial_count, target_count):
        # Mix adjacent placement with random placement for better coverage
        use_random = (i % 5 == 0) or (len(placed_rects) < 10)  # Every 5th or if few rectangles
        
        if use_random:
            rect = _place_random_rectangle(
                spatial_grid, width, height, min_size, max_size,
                aspect_ratio_variance, rng, max_placement_attempts, adjacency_tolerance
            )
        else:
            rect = _place_adjacent_rectangle(
                placed_rects, spatial_grid, width, height, min_size, max_size, 
                aspect_ratio_variance, rng, max_placement_attempts, adjacency_tolerance
            )
        
        total_attempts += max_placement_attempts if rect is None else (i % 10 + 1)
        
        if rect is not None:
            placed_rects.append(rect)
            spatial_grid.add_rectangle(rect)
            if verbose and (i < 10 or i % 100 == 0):
                x, y, w, h = rect
                print(f"[rectangles] Placed #{i}: {w:.1f}x{h:.1f} at ({x:.1f},{y:.1f})")
        else:
            failed_placements += 1
            
        # Early termination if too many failures
        if failed_placements > target_count * 0.2:
            if verbose:
                print(f"[rectangles] Early termination: {failed_placements} failures")
            break
    
    # More aggressive cascade fill
    if cascade_fill_enabled:
        remaining = target_count - len(placed_rects)
        if remaining > 0:
            if verbose:
                print(f"[rectangles] Starting cascade fill for {remaining} remaining rectangles")
            
            cascade_rects = _cascade_fill(
                placed_rects, spatial_grid, width, height, 
                min_size * 0.3, min_size * 0.8, aspect_ratio_variance, rng, 
                remaining, max_placement_attempts * 2
            )
            placed_rects.extend(cascade_rects)
            
            if verbose:
                print(f"[rectangles] Cascade fill added {len(cascade_rects)} rectangles")
    
    # Calculate actual space utilization
    total_rect_area = sum(w * h for _, _, w, h in placed_rects)
    utilization = (total_rect_area / canvas_area) * 100
    
    if verbose:
        print(f"[rectangles] Final count: {len(placed_rects)}/{target_count} rectangles")
        print(f"[rectangles] Space utilization: {utilization:.1f}%")
        print(f"[rectangles] Failed placements: {failed_placements}")
    
    # Convert to shape format with color sampling
    shapes: List[Dict] = []
    for i, (x, y, w, h) in enumerate(placed_rects):
        # Calculate rectangle center for color sampling
        center_x = x + w / 2
        center_y = y + h / 2
        
        color = _sample_image_color(input_image, center_x, center_y, width, height)
        
        shapes.append({
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
    
    return shapes


def _generate_rectangle_size(
    min_size: float, 
    max_size: float, 
    aspect_variance: float, 
    rng: random.Random
) -> Tuple[float, float]:
    """Generate width and height with proper aspect ratio variation."""
    # Base size
    base = rng.uniform(min_size, max_size)
    
    # Aspect ratio variation (1/variance to variance)
    aspect_ratio = rng.uniform(1.0 / aspect_variance, aspect_variance)
    
    # Apply aspect ratio
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
    """
    Place a rectangle at a random position for better canvas coverage.
    """
    for attempt in range(max_attempts):
        # Generate rectangle with proper aspect ratio
        w, h = _generate_rectangle_size(min_size, max_size, aspect_variance, rng)
        
        # Random position with edge bias occasionally
        if attempt < max_attempts // 3:
            # Pure random placement
            x = rng.uniform(0, canvas_width - w)
            y = rng.uniform(0, canvas_height - h)
        else:
            # Edge-biased placement for better coverage
            edge_margin = min(w, h) * 2
            if rng.random() < 0.5:
                # Bias toward edges
                if rng.random() < 0.5:
                    x = rng.uniform(0, edge_margin)  # Left edge
                else:
                    x = rng.uniform(canvas_width - w - edge_margin, canvas_width - w)  # Right edge
                y = rng.uniform(0, canvas_height - h)
            else:
                # Bias toward top/bottom
                x = rng.uniform(0, canvas_width - w)
                if rng.random() < 0.5:
                    y = rng.uniform(0, edge_margin)  # Top edge
                else:
                    y = rng.uniform(canvas_height - h - edge_margin, canvas_height - h)  # Bottom edge
        
        # Ensure within bounds
        x = max(0, min(canvas_width - w, x))
        y = max(0, min(canvas_height - h, y))
        
        candidate_rect = (x, y, w, h)
        
        # Check for overlaps
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
    """
    Find a valid adjacent position for a new rectangle with better placement logic.
    """
    
    for attempt in range(max_attempts):
        # Generate rectangle with proper aspect ratio
        w, h = _generate_rectangle_size(min_size, max_size, aspect_variance, rng)
        
        # Pick a random existing rectangle to be adjacent to
        target_rect = rng.choice(existing_rects)
        tx, ty, tw, th = target_rect
        
        # Generate more candidate positions with better overlap
        candidate_positions = [
            # Right side - more positions
            (tx + tw + tolerance, ty + rng.uniform(-h * 0.7, th - h * 0.3)),
            (tx + tw + tolerance, ty + rng.uniform(-h * 0.3, th - h * 0.7)),
            # Left side
            (tx - w - tolerance, ty + rng.uniform(-h * 0.7, th - h * 0.3)),
            (tx - w - tolerance, ty + rng.uniform(-h * 0.3, th - h * 0.7)),
            # Bottom side
            (tx + rng.uniform(-w * 0.7, tw - w * 0.3), ty + th + tolerance),
            (tx + rng.uniform(-w * 0.3, tw - w * 0.7), ty + th + tolerance),
            # Top side
            (tx + rng.uniform(-w * 0.7, tw - w * 0.3), ty - h - tolerance),
            (tx + rng.uniform(-w * 0.3, tw - w * 0.7), ty - h - tolerance),
            # Corner positions
            (tx + tw + tolerance, ty + th + tolerance),  # bottom-right
            (tx - w - tolerance, ty + th + tolerance),   # bottom-left
            (tx + tw + tolerance, ty - h - tolerance),   # top-right
            (tx - w - tolerance, ty - h - tolerance),    # top-left
        ]
        
        # Try each candidate position
        for x, y in candidate_positions:
            # Check canvas bounds with small margin
            margin = 1.0
            if x < -margin or y < -margin or x + w > canvas_width + margin or y + h > canvas_height + margin:
                continue
                
            # Clamp to canvas bounds
            x = max(0, min(canvas_width - w, x))
            y = max(0, min(canvas_height - h, y))
            
            candidate_rect = (x, y, w, h)
            
            # Check for overlaps with existing rectangles
            if not spatial_grid.has_collision(candidate_rect, tolerance * 0.5):
                return candidate_rect
    
    return None


def _cascade_fill(
    existing_rects: List[Tuple[float, float, float, float]],
    spatial_grid: 'SpatialGrid',
    canvas_width: int,
    canvas_height: int,
    min_fill_size: float,
    max_fill_size: float,
    aspect_variance: float,
    rng: random.Random,
    max_fill_count: int,
    max_attempts: int
) -> List[Tuple[float, float, float, float]]:
    """
    More aggressive gap filling with edge priority for better canvas coverage.
    """
    fill_rects: List[Tuple[float, float, float, float]] = []
    
    # Define edge regions for prioritized filling
    edge_margin = max_fill_size * 2
    edge_regions = [
        (0, 0, edge_margin, canvas_height),  # Left edge
        (canvas_width - edge_margin, 0, edge_margin, canvas_height),  # Right edge  
        (0, 0, canvas_width, edge_margin),  # Top edge
        (0, canvas_height - edge_margin, canvas_width, edge_margin),  # Bottom edge
    ]
    
    for i in range(max_fill_count):
        placed = False
        
        for attempt in range(max_attempts):
            # Generate small rectangle with aspect variation
            w, h = _generate_rectangle_size(min_fill_size, max_fill_size, aspect_variance, rng)
            
            # Placement strategy based on progress
            if i < max_fill_count * 0.3:
                # First 30%: Prioritize edges for coverage
                region = rng.choice(edge_regions)
                region_x, region_y, region_w, region_h = region
                x = rng.uniform(region_x, max(region_x, region_x + region_w - w))
                y = rng.uniform(region_y, max(region_y, region_y + region_h - h))
                # Clamp to canvas
                x = max(0, min(canvas_width - w, x))
                y = max(0, min(canvas_height - h, y))
                
            elif i < max_fill_count * 0.7:
                # Middle 40%: Adjacent to existing rectangles
                if existing_rects or fill_rects:
                    all_rects = existing_rects + fill_rects
                    target = rng.choice(all_rects)
                    tx, ty, tw, th = target
                    
                    # More diverse adjacent positions
                    positions = [
                        (tx + tw + 0.5, ty + rng.uniform(-h*0.5, th-h*0.5)),
                        (tx - w - 0.5, ty + rng.uniform(-h*0.5, th-h*0.5)),
                        (tx + rng.uniform(-w*0.5, tw-w*0.5), ty + th + 0.5),
                        (tx + rng.uniform(-w*0.5, tw-w*0.5), ty - h - 0.5),
                        (tx + tw + 0.5, ty + th + 0.5),  # corner positions
                        (tx - w - 0.5, ty - h - 0.5),
                    ]
                    
                    pos = rng.choice(positions)
                    x, y = pos
                    
                    # Clamp to bounds
                    x = max(0, min(canvas_width - w, x))
                    y = max(0, min(canvas_height - h, y))
                else:
                    # Fallback to random
                    x = rng.uniform(0, canvas_width - w)
                    y = rng.uniform(0, canvas_height - h)
            else:
                # Final 30%: Pure random for gap filling
                x = rng.uniform(0, canvas_width - w)
                y = rng.uniform(0, canvas_height - h)
            
            candidate_rect = (x, y, w, h)
            
            # Check for overlaps with minimal tolerance for denser packing
            if not spatial_grid.has_collision(candidate_rect, tolerance=0.25):
                fill_rects.append(candidate_rect)
                spatial_grid.add_rectangle(candidate_rect)
                placed = True
                break
        
        if not placed and i > max_fill_count * 0.6:
            # Stop if we can't place rectangles in the final portion
            break
    
    return fill_rects


class SpatialGrid:
    """
    Spatial grid for efficient collision detection.
    """
    
    def __init__(self, width: int, height: int, grid_size: int = 32):
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.cols = max(1, width // grid_size)
        self.rows = max(1, height // grid_size)
        self.cell_width = width / self.cols
        self.cell_height = height / self.rows
        
        # Grid of sets containing rectangle indices
        self.grid: List[List[Set[int]]] = [
            [set() for _ in range(self.cols)] for _ in range(self.rows)
        ]
        self.rectangles: List[Tuple[float, float, float, float]] = []
    
    def add_rectangle(self, rect: Tuple[float, float, float, float]) -> int:
        """Add rectangle to spatial grid and return its index."""
        rect_idx = len(self.rectangles)
        self.rectangles.append(rect)
        
        # Find all grid cells this rectangle overlaps
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
        
        # Find potentially overlapping grid cells
        start_col = max(0, int(x // self.cell_width))
        end_col = min(self.cols - 1, int((x + w) // self.cell_width))
        start_row = max(0, int(y // self.cell_height))
        end_row = min(self.rows - 1, int((y + h) // self.cell_height))
        
        # Check all rectangles in overlapping cells
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
    """Check if two rectangles overlap (with optional tolerance for adjacency)."""
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    
    # Add tolerance to create buffer zone
    return not (
        x1 + w1 <= x2 - tolerance or  # rect1 is to the left of rect2
        x2 + w2 <= x1 - tolerance or  # rect2 is to the left of rect1
        y1 + h1 <= y2 - tolerance or  # rect1 is above rect2
        y2 + h2 <= y1 - tolerance     # rect2 is above rect1
    )


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


def register(register_fn) -> None:
    register_fn(PLUGIN_NAME, generate)