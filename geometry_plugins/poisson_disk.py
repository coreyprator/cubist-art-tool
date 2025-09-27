# Poisson disk sampling plugin for Cubist Art
# Generates blue noise point distribution with minimum distance between points

from __future__ import annotations
import math
import random
from typing import List, Tuple


def poisson_disk_sampling(
    canvas_size: Tuple[int, int],
    total_points: int = 1000,
    seed: int = 0,
    min_dist_factor: float = 0.025,  # minimum distance as fraction of canvas size
    k: int = 30,  # number of attempts before rejection
    **kwargs,
) -> List[Tuple[float, float]]:
    """
    Generate Poisson disk sampling (blue noise).

    Args:
        canvas_size: (width, height) tuple
        total_points: Target number of points to generate
        seed: Random seed
        min_dist_factor: Minimum distance between points as fraction of canvas diagonal
        k: Number of attempts before rejection

    Returns:
        List of (x, y) points
    """
    width, height = canvas_size

    # Set seed for reproducibility
    random.seed(seed)

    # Calculate minimum distance between points (scaled by canvas size)
    diagonal = math.sqrt(width * width + height * height)
    min_dist = diagonal * min_dist_factor

    # Grid cell size (slightly larger than min_dist/sqrt(2) for optimization)
    cell_size = min_dist / math.sqrt(2)
    grid_width = int(math.ceil(width / cell_size))
    grid_height = int(math.ceil(height / cell_size))

    # Initialize grid
    grid = [None] * (grid_width * grid_height)

    # Helper functions
    def get_cell_idx(x: float, y: float) -> int:
        cell_x = int(x / cell_size)
        cell_y = int(y / cell_size)
        return (
            cell_x + cell_y * grid_width
            if 0 <= cell_x < grid_width and 0 <= cell_y < grid_height
            else -1
        )

    def get_neighbors(x: float, y: float) -> List[Tuple[float, float]]:
        neighbors = []

        # Get the cell coordinates
        cell_x = int(x / cell_size)
        cell_y = int(y / cell_size)

        # Check surrounding cells
        for i in range(max(0, cell_x - 2), min(grid_width, cell_x + 3)):
            for j in range(max(0, cell_y - 2), min(grid_height, cell_y + 3)):
                idx = i + j * grid_width
                if 0 <= idx < len(grid) and grid[idx] is not None:
                    neighbors.append(grid[idx])

        return neighbors

    def is_valid(x: float, y: float) -> bool:
        if not (0 <= x < width and 0 <= y < height):
            return False

        cell_idx = get_cell_idx(x, y)
        if cell_idx == -1:
            return False

        neighbors = get_neighbors(x, y)
        for nx, ny in neighbors:
            dx = x - nx
            dy = y - ny
            if dx * dx + dy * dy < min_dist * min_dist:
                return False

        return True

    # Main algorithm
    active_points: List[Tuple[float, float]] = []
    points: List[Tuple[float, float]] = []

    # Start with a random point
    first_x = random.uniform(0, width)
    first_y = random.uniform(0, height)
    active_points.append((first_x, first_y))
    points.append((first_x, first_y))

    cell_idx = get_cell_idx(first_x, first_y)
    if cell_idx >= 0:
        grid[cell_idx] = (first_x, first_y)

    # While there are active points and we haven't reached the target count
    while active_points and len(points) < total_points:
        # Get random active point
        idx = random.randint(0, len(active_points) - 1)
        x, y = active_points[idx]

        # Try to find a new point
        found = False
        for _ in range(k):
            # Generate a random point at a distance between min_dist and 2*min_dist
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(min_dist, 2 * min_dist)
            new_x = x + radius * math.cos(angle)
            new_y = y + radius * math.sin(angle)

            if is_valid(new_x, new_y):
                active_points.append((new_x, new_y))
                points.append((new_x, new_y))

                cell_idx = get_cell_idx(new_x, new_y)
                if cell_idx >= 0:
                    grid[cell_idx] = (new_x, new_y)

                found = True

                # Break if we've reached the target count
                if len(points) >= total_points:
                    break

        # If no valid point was found after k attempts, remove the active point
        if not found:
            active_points.pop(idx)

    return points


def generate(canvas_size, total_points=1000, seed=0, input_image=None, **kwargs):
    """Generate Poisson disk sampling and return shapes for SVG export.

    Args:
        canvas_size: (width, height) tuple
        total_points: Maximum number of points to generate
        seed: Random seed for reproducibility
        input_image: PIL Image object for color sampling
        **kwargs: Additional parameters

    Returns:
        List of circle dictionaries with 'type', 'cx', 'cy', 'r' keys
    """
    # Get the base points
    try:
        points = poisson_disk_sampling(canvas_size, total_points, seed, **kwargs)
    except Exception as e:
        print(f"Error in poisson_disk_sampling: {e}")
        # Fallback to random points if sampling fails
        random.seed(seed)
        points = []
        width, height = canvas_size
        for _ in range(total_points):
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            points.append((x, y))

    # Determine radius - smaller radius for more points to avoid overlap
    width, height = canvas_size
    area = width * height
    avg_area_per_point = area / max(1, len(points))
    point_radius = math.sqrt(avg_area_per_point) * 0.25  # Adjust this factor as needed

    # Convert points to circle shapes for SVG export
    shapes = []
    for x, y in points:
        shapes.append(
            {
                "type": "circle",
                "cx": float(x),
                "cy": float(y),
                "r": float(point_radius),
                "fill": _sample_image_color(input_image, x, y, width, height),
                "stroke": "none",
            }
        )

    return shapes


def _sample_image_color(input_image, x: float, y: float, canvas_width: int, canvas_height: int) -> Tuple[int, int, int]:
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