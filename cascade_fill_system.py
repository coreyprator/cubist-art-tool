# cascade_fill_system.py - Universal Cascade Fill for All Geometries
# Cubist Art v2.5.0 - Priority 1 Implementation

from __future__ import annotations
import random
import math
from typing import Dict, List, Tuple, Optional, Set, Callable, Any

class SpatialGrid:
    """
    Universal spatial grid for efficient collision detection across all geometry types.
    Extracted and enhanced from rectangles.py implementation.
    """
    
    def __init__(self, width: int, height: int, grid_size: int = 32):
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.cols = max(1, width // grid_size)
        self.rows = max(1, height // grid_size)
        self.cell_width = width / self.cols
        self.cell_height = height / self.rows
        
        # Grid of sets containing shape indices
        self.grid: List[List[Set[int]]] = [
            [set() for _ in range(self.cols)] for _ in range(self.rows)
        ]
        self.shapes: List[Dict] = []
    
    def add_shape(self, shape: Dict) -> int:
        """Add any shape type to spatial grid and return its index."""
        shape_idx = len(self.shapes)
        self.shapes.append(shape)
        
        # Get bounding box for this shape
        bbox = self._get_shape_bbox(shape)
        if bbox:
            x_min, y_min, x_max, y_max = bbox
            
            # Find all grid cells this shape overlaps
            start_col = max(0, int(x_min // self.cell_width))
            end_col = min(self.cols - 1, int(x_max // self.cell_width))
            start_row = max(0, int(y_min // self.cell_height))
            end_row = min(self.rows - 1, int(y_max // self.cell_height))
            
            for row in range(start_row, end_row + 1):
                for col in range(start_col, end_col + 1):
                    self.grid[row][col].add(shape_idx)
        
        return shape_idx
    
    def _get_shape_bbox(self, shape: Dict) -> Optional[Tuple[float, float, float, float]]:
        """Get bounding box (x_min, y_min, x_max, y_max) for any shape type."""
        shape_type = shape.get("type", "").lower()
        
        if shape_type == "circle":
            cx, cy, r = shape.get("cx", 0), shape.get("cy", 0), shape.get("r", 1)
            return (cx - r, cy - r, cx + r, cy + r)
        
        elif shape_type in ("rect", "rectangle"):
            x, y = shape.get("x", 0), shape.get("y", 0)
            w, h = shape.get("w", 1), shape.get("h", 1)
            return (x, y, x + w, y + h)
        
        elif "points" in shape and shape["points"]:
            points = shape["points"]
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
        
        # Fallback for unknown shape types
        return None
    
    def has_collision(self, test_shape: Dict, tolerance: float = 0.0) -> bool:
        """Check if test shape collides with any existing shapes."""
        test_bbox = self._get_shape_bbox(test_shape)
        if not test_bbox:
            return False
        
        x_min, y_min, x_max, y_max = test_bbox
        
        # Find potentially overlapping grid cells
        start_col = max(0, int(x_min // self.cell_width))
        end_col = min(self.cols - 1, int(x_max // self.cell_width))
        start_row = max(0, int(y_min // self.cell_height))
        end_row = min(self.rows - 1, int(y_max // self.cell_height))
        
        # Check all shapes in overlapping cells
        checked_shapes: Set[int] = set()
        
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                for shape_idx in self.grid[row][col]:
                    if shape_idx in checked_shapes:
                        continue
                    checked_shapes.add(shape_idx)
                    
                    existing_shape = self.shapes[shape_idx]
                    if self._shapes_overlap(test_shape, existing_shape, tolerance):
                        return True
        
        return False
    
    def _shapes_overlap(self, shape1: Dict, shape2: Dict, tolerance: float) -> bool:
        """Check if two shapes overlap (works for any shape type)."""
        bbox1 = self._get_shape_bbox(shape1)
        bbox2 = self._get_shape_bbox(shape2)
        
        if not bbox1 or not bbox2:
            return False
        
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        # Bounding box overlap test with tolerance
        return not (
            x1_max <= x2_min - tolerance or
            x2_max <= x1_min - tolerance or
            y1_max <= y2_min - tolerance or
            y2_max <= y1_min - tolerance
        )
    
    def get_shapes_in_region(self, x: float, y: float, width: float, height: float) -> List[Dict]:
        """Get all shapes that might be in the specified region."""
        start_col = max(0, int(x // self.cell_width))
        end_col = min(self.cols - 1, int((x + width) // self.cell_width))
        start_row = max(0, int(y // self.cell_height))
        end_row = min(self.rows - 1, int((y + height) // self.cell_height))
        
        shape_indices: Set[int] = set()
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                shape_indices.update(self.grid[row][col])
        
        return [self.shapes[i] for i in shape_indices]


class CascadeFillSystem:
    """
    Universal cascade fill system that works with any geometry type.
    Provides gap detection and intelligent space utilization.
    """
    
    def __init__(self, canvas_width: int, canvas_height: int, rng: random.Random):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.rng = rng
    
    def apply_cascade_fill(
        self,
        existing_shapes: List[Dict],
        spatial_grid: SpatialGrid,
        target_count: int,
        shape_generator: Callable[[], Dict],
        min_size: float = 2.0,
        max_attempts: int = 100,
        verbose: bool = False
    ) -> List[Dict]:
        """
        Apply cascade fill to any geometry type.
        
        Args:
            existing_shapes: List of already placed shapes
            spatial_grid: Spatial grid containing existing shapes
            target_count: Desired total number of shapes
            shape_generator: Function that returns a new shape dict
            min_size: Minimum size for cascade shapes
            max_attempts: Maximum placement attempts per shape
            verbose: Enable debug logging
        
        Returns:
            List of new shapes added by cascade fill
        """
        remaining = target_count - len(existing_shapes)
        if remaining <= 0:
            return []
        
        if verbose:
            print(f"[cascade_fill] Starting cascade fill for {remaining} shapes")
        
        cascade_shapes: List[Dict] = []
        
        # Define fill strategies based on canvas regions
        edge_regions = self._get_edge_regions()
        gap_regions = self._detect_gap_regions(existing_shapes)
        
        for i in range(remaining):
            placed = False
            
            for attempt in range(max_attempts):
                # Generate a new shape
                candidate_shape = shape_generator()
                
                # Apply placement strategy based on progress
                if i < remaining * 0.3:
                    # First 30%: Fill edge regions for better coverage
                    candidate_shape = self._position_in_edges(candidate_shape, edge_regions)
                elif i < remaining * 0.7:
                    # Middle 40%: Fill detected gaps
                    candidate_shape = self._position_in_gaps(candidate_shape, gap_regions)
                else:
                    # Final 30%: Random placement for remaining gaps
                    candidate_shape = self._position_randomly(candidate_shape)
                
                # Ensure shape is within canvas bounds
                candidate_shape = self._clamp_to_canvas(candidate_shape)
                
                # Check for collisions with minimal tolerance for dense packing
                if not spatial_grid.has_collision(candidate_shape, tolerance=0.25):
                    cascade_shapes.append(candidate_shape)
                    spatial_grid.add_shape(candidate_shape)
                    placed = True
                    break
            
            if not placed and i > remaining * 0.6:
                # Stop if we can't place shapes in the final portion
                if verbose:
                    print(f"[cascade_fill] Early termination after {len(cascade_shapes)} shapes")
                break
        
        if verbose:
            print(f"[cascade_fill] Added {len(cascade_shapes)} cascade shapes")
        
        return cascade_shapes
    
    def _get_edge_regions(self) -> List[Tuple[float, float, float, float]]:
        """Define edge regions for prioritized filling."""
        edge_margin = min(self.canvas_width, self.canvas_height) * 0.1
        
        return [
            (0, 0, edge_margin, self.canvas_height),  # Left edge
            (self.canvas_width - edge_margin, 0, edge_margin, self.canvas_height),  # Right edge
            (0, 0, self.canvas_width, edge_margin),  # Top edge
            (0, self.canvas_height - edge_margin, self.canvas_width, edge_margin),  # Bottom edge
        ]
    
    def _detect_gap_regions(self, existing_shapes: List[Dict]) -> List[Tuple[float, float, float, float]]:
        """Detect gaps in the existing shape layout."""
        # Simple grid-based gap detection
        grid_size = 50
        cell_width = self.canvas_width / grid_size
        cell_height = self.canvas_height / grid_size
        
        # Mark occupied cells
        occupied = [[False for _ in range(grid_size)] for _ in range(grid_size)]
        
        for shape in existing_shapes:
            bbox = self._get_shape_bbox(shape)
            if bbox:
                x_min, y_min, x_max, y_max = bbox
                start_col = max(0, int(x_min / cell_width))
                end_col = min(grid_size - 1, int(x_max / cell_width))
                start_row = max(0, int(y_min / cell_height))
                end_row = min(grid_size - 1, int(y_max / cell_height))
                
                for row in range(start_row, end_row + 1):
                    for col in range(start_col, end_col + 1):
                        occupied[row][col] = True
        
        # Find gap regions (clusters of empty cells)
        gap_regions = []
        for row in range(0, grid_size, 5):  # Check every 5th cell
            for col in range(0, grid_size, 5):
                if not occupied[row][col]:
                    # Found a gap, create a region around it
                    x = col * cell_width
                    y = row * cell_height
                    w = min(cell_width * 5, self.canvas_width - x)
                    h = min(cell_height * 5, self.canvas_height - y)
                    gap_regions.append((x, y, w, h))
        
        return gap_regions
    
    def _get_shape_bbox(self, shape: Dict) -> Optional[Tuple[float, float, float, float]]:
        """Get bounding box for any shape type - duplicate of SpatialGrid method."""
        shape_type = shape.get("type", "").lower()
        
        if shape_type == "circle":
            cx, cy, r = shape.get("cx", 0), shape.get("cy", 0), shape.get("r", 1)
            return (cx - r, cy - r, cx + r, cy + r)
        
        elif shape_type in ("rect", "rectangle"):
            x, y = shape.get("x", 0), shape.get("y", 0)
            w, h = shape.get("w", 1), shape.get("h", 1)
            return (x, y, x + w, y + h)
        
        elif "points" in shape and shape["points"]:
            points = shape["points"]
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
        
        return None
    
    def _position_in_edges(self, shape: Dict, edge_regions: List[Tuple[float, float, float, float]]) -> Dict:
        """Position shape in edge regions."""
        region = self.rng.choice(edge_regions)
        region_x, region_y, region_w, region_h = region
        
        bbox = self._get_shape_bbox(shape)
        if bbox:
            _, _, shape_w, shape_h = bbox
            x = self.rng.uniform(region_x, max(region_x, region_x + region_w - shape_w))
            y = self.rng.uniform(region_y, max(region_y, region_y + region_h - shape_h))
            return self._translate_shape(shape, x, y)
        
        return shape
    
    def _position_in_gaps(self, shape: Dict, gap_regions: List[Tuple[float, float, float, float]]) -> Dict:
        """Position shape in detected gap regions."""
        if not gap_regions:
            return self._position_randomly(shape)
        
        region = self.rng.choice(gap_regions)
        region_x, region_y, region_w, region_h = region
        
        bbox = self._get_shape_bbox(shape)
        if bbox:
            _, _, shape_w, shape_h = bbox
            x = self.rng.uniform(region_x, max(region_x, region_x + region_w - shape_w))
            y = self.rng.uniform(region_y, max(region_y, region_y + region_h - shape_h))
            return self._translate_shape(shape, x, y)
        
        return shape
    
    def _position_randomly(self, shape: Dict) -> Dict:
        """Position shape randomly on canvas."""
        bbox = self._get_shape_bbox(shape)
        if bbox:
            _, _, shape_w, shape_h = bbox
            x = self.rng.uniform(0, max(0, self.canvas_width - shape_w))
            y = self.rng.uniform(0, max(0, self.canvas_height - shape_h))
            return self._translate_shape(shape, x, y)
        
        return shape
    
    def _translate_shape(self, shape: Dict, new_x: float, new_y: float) -> Dict:
        """Translate shape to new position."""
        shape_copy = shape.copy()
        shape_type = shape.get("type", "").lower()
        
        if shape_type == "circle":
            shape_copy["cx"] = new_x
            shape_copy["cy"] = new_y
        elif shape_type in ("rect", "rectangle"):
            shape_copy["x"] = new_x
            shape_copy["y"] = new_y
        elif "points" in shape:
            # Calculate current centroid
            points = shape["points"]
            if points:
                cx = sum(p[0] for p in points) / len(points)
                cy = sum(p[1] for p in points) / len(points)
                # Translate all points
                dx, dy = new_x - cx, new_y - cy
                shape_copy["points"] = [(p[0] + dx, p[1] + dy) for p in points]
        
        return shape_copy
    
    def _clamp_to_canvas(self, shape: Dict) -> Dict:
        """Ensure shape is within canvas bounds."""
        bbox = self._get_shape_bbox(shape)
        if not bbox:
            return shape
        
        x_min, y_min, x_max, y_max = bbox
        
        # Calculate clamping offsets
        dx = 0
        dy = 0
        
        if x_min < 0:
            dx = -x_min
        elif x_max > self.canvas_width:
            dx = self.canvas_width - x_max
        
        if y_min < 0:
            dy = -y_min
        elif y_max > self.canvas_height:
            dy = self.canvas_height - y_max
        
        if dx != 0 or dy != 0:
            return self._translate_shape(shape, bbox[0] + dx, bbox[1] + dy)
        
        return shape


# Utility functions for geometry plugins

def apply_universal_cascade_fill(
    shapes: List[Dict],
    canvas_size: Tuple[int, int],
    target_count: int,
    shape_generator: Callable[[], Dict],
    seed: int = 42,
    verbose: bool = False
) -> List[Dict]:
    """
    Easy-to-use function for applying cascade fill to any geometry plugin.
    
    Usage in geometry plugins:
    ```python
    from cascade_fill_system import apply_universal_cascade_fill
    
    def generate_small_circle():
        return {
            "type": "circle",
            "cx": 0, "cy": 0,  # Will be positioned by cascade fill
            "r": random.uniform(2, 8),
            "fill": "rgb(128,128,128)"
        }
    
    # Apply cascade fill
    enhanced_shapes = apply_universal_cascade_fill(
        shapes=initial_shapes,
        canvas_size=canvas_size,
        target_count=total_points,
        shape_generator=generate_small_circle,
        verbose=True
    )
    ```
    """
    width, height = canvas_size
    rng = random.Random(seed)
    
    # Create spatial grid with existing shapes
    spatial_grid = SpatialGrid(width, height)
    for shape in shapes:
        spatial_grid.add_shape(shape)
    
    # Apply cascade fill
    cascade_system = CascadeFillSystem(width, height, rng)
    cascade_shapes = cascade_system.apply_cascade_fill(
        existing_shapes=shapes,
        spatial_grid=spatial_grid,
        target_count=target_count,
        shape_generator=shape_generator,
        verbose=verbose
    )
    
    # Return combined shapes
    return shapes + cascade_shapes


def sample_image_color(
    input_image, x: float, y: float, canvas_width: int, canvas_height: int
) -> str:
    """
    Universal color sampling function for all geometry plugins.
    Samples color from input image at given coordinates.
    """
    if input_image is None:
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
