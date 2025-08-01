# GOAL: Implement actual triangulation logic to replace placeholder stub.
# FILE AFFECTED: cubist_core_logic.py
# INTERFACE IMPACT: None – this affects only backend logic, no GUI or CLI changes.
# VALIDATION: Visual inspection of the output image will confirm triangulation is correctly rendered.
# VERSION: v12j – update inline version footer and comments to reflect new logic.
# CHANGELOG: To be updated separately once testing is complete.
"""
Cubist Art Generator Core Logic

__version__ = "v12d"
__author__ = "Corey Prator"
__date__ = "2025-07-27"
"""

# Import logging
from cubist_logger import logger

def run_cubist(input_path, output_dir, mask_path=None, total_points=1000, clip_to_alpha=True, verbose=True, geometry_mode="delaunay", use_cascade_fill=False, save_step_frames=False):
    """
    Generate a cubist-style image using the specified geometry mode.

    Args:
        input_path (str): Path to input image.
        output_dir (str): Directory to save output.
        mask_path (str, optional): Path to mask image.
        total_points (int): Number of points to sample.
        clip_to_alpha (bool): Whether to clip to alpha/mask.
        verbose (bool): Print output path if True.
        geometry_mode (str): Geometry mode ('delaunay', 'voronoi', 'rectangles').
        use_cascade_fill (bool): Use CascadeFill logic instead of regular tessellation.
        save_step_frames (bool): Save intermediate frames for animation (future feature).

    Returns:
        str: Path to output image.
    """
    logger.info(f"run_cubist() ENTRY: mode={geometry_mode}, cascade_fill={use_cascade_fill}, points={total_points}")
    
    import cv2
    import numpy as np
    from pathlib import Path
    import os

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Created output directory: {output_dir}")

    # Load input image (with alpha)
    logger.info(f"Loading input image: {input_path}")
    image_bgra = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
    if image_bgra is None:
        logger.error(f"Input image not found: {input_path}")
        raise FileNotFoundError(f"Input image not found: {input_path}")
    if image_bgra.shape[2] == 4:
        image_rgb = cv2.cvtColor(image_bgra[:, :, :3], cv2.COLOR_BGR2RGB)
        alpha = image_bgra[:, :, 3]
        logger.info(f"Loaded RGBA image: {image_bgra.shape}")
    else:
        image_rgb = cv2.cvtColor(image_bgra, cv2.COLOR_BGR2RGB)
        alpha = np.ones(image_rgb.shape[:2], dtype=np.uint8) * 255
        logger.info(f"Loaded RGB image: {image_bgra.shape}")
    height, width = image_rgb.shape[:2]

    # Load mask if provided
    if mask_path is not None:
        logger.info(f"Loading mask: {mask_path}")
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if mask is None or mask.shape != (height, width):
            logger.error(f"Mask not found or size mismatch: {mask_path}")
            raise ValueError(f"Mask not found or size mismatch: {mask_path}")
        valid_mask = (mask > 0) & (alpha > 0)
        logger.info(f"Using mask with {np.sum(valid_mask)} valid pixels")
    else:
        valid_mask = (alpha > 0)
        logger.info(f"No mask provided, using alpha channel with {np.sum(valid_mask)} valid pixels")

    # Sample points from valid region
    valid_coords = np.argwhere(valid_mask)
    if len(valid_coords) < 4:
        logger.error("Not enough valid pixels to sample points")
        raise ValueError("Not enough valid pixels to sample points.")
    idxs = np.random.choice(valid_coords.shape[0], min(total_points, len(valid_coords)), replace=False)
    pts = valid_coords[idxs][:, [1, 0]]  # (x, y)
    logger.info(f"Sampled {len(pts)} points from valid region")

    # Add corners
    corners = np.array([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]])
    pts = np.vstack([pts, corners])
    logger.info(f"Added corners, total points: {len(pts)}")

    # Generate geometry (triangles, polygons, etc.)
    logger.info(f"Starting geometry generation: mode={geometry_mode}, cascade_fill={use_cascade_fill}")
    if use_cascade_fill:
        # Use CascadeFill logic instead of regular tessellation
        logger.info("Using CascadeFill logic for geometry generation")
        canvas = generate_cascade_fill(image_rgb, valid_mask, (height, width), geometry_mode, total_points, save_step_frames, output_dir if save_step_frames else None)
    else:
        # Use regular tessellation approach
        logger.info("Using regular tessellation approach")
        geometry = generate_geometry(pts, (height, width), geometry_mode, use_cascade_fill=False)
        canvas = render_geometry(image_rgb, valid_mask, geometry, pts, geometry_mode)

    # Preserve alpha in output
    canvas_rgba = np.dstack((canvas, alpha))
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Update output filename to include cascade flag and mask status
    cascade_flag = "cascade" if use_cascade_fill else "regular"
    mask_flag = "_masked" if mask_path is not None else ""
    output_name = f"your_input_image_{total_points:05d}pts_{geometry_mode}_{cascade_flag}{mask_flag}_{timestamp}.png"
    output_path = Path(output_dir) / output_name
    logger.info(f"Saving output to: {output_path}")
    cv2.imwrite(str(output_path), cv2.cvtColor(canvas_rgba, cv2.COLOR_RGBA2BGRA))
    if verbose:
        print(f"Saved: {os.path.abspath(str(output_path))}")
    logger.info(f"run_cubist() EXIT: Successfully saved {output_path}")
    return str(output_path)


def generate_geometry(points, image_shape, mode, use_cascade_fill=False):
    """
    Dispatch geometry generation based on mode.
    Args:
        points (np.ndarray): Array of (x, y) points.
        image_shape (tuple): (height, width) of the image.
        mode (str): Geometry mode ('delaunay', 'voronoi', 'rectangles').
        use_cascade_fill (bool): Whether to use CascadeFill logic (not used in regular tessellation).
    Returns:
        Geometry object (Delaunay, Voronoi, or placeholder)
    Raises:
        ValueError: If mode is not supported.
    """
    logger.info(f"generate_geometry() ENTRY: mode={mode}, points={len(points)}")
    from scipy.spatial import Delaunay, Voronoi
    import numpy as np
    if mode == "delaunay":
        logger.info("Creating Delaunay triangulation")
        result = Delaunay(points)
        logger.info(f"Created Delaunay with {len(result.simplices)} triangles")
        return result
    elif mode == "voronoi":
        logger.info("Creating Voronoi diagram")
        result = Voronoi(points)
        logger.info(f"Created Voronoi with {len(result.vertices)} vertices")
        return result
    elif mode == "rectangles":
        logger.info("Rectangle mode - no geometry object needed")
        return None
    else:
        logger.error(f"Unsupported geometry mode: {mode}")
        raise ValueError(f"Unsupported geometry mode: {mode}")


def render_geometry(image_rgb, valid_mask, geometry, points, mode):
    """
    Render geometry shapes onto a canvas using the original tessellation approach.
    
    Args:
        image_rgb (np.ndarray): Source image in RGB format.
        valid_mask (np.ndarray): Boolean mask of valid pixels.
        geometry: Geometry object from generate_geometry().
        points (np.ndarray): Array of (x, y) points.
        mode (str): Geometry mode ('delaunay', 'voronoi', 'rectangles').
    
    Returns:
        np.ndarray: Rendered canvas in RGB format.
    """
    logger.info(f"render_geometry() ENTRY: mode={mode}")
    import cv2
    import numpy as np
    
    height, width = image_rgb.shape[:2]
    canvas = np.zeros_like(image_rgb)
    
    if mode == "delaunay":
        logger.info(f"Rendering Delaunay triangles: {len(geometry.simplices)} triangles")
        rendered_count = 0
        for simplex in geometry.simplices:
            tri_pts = points[simplex].astype(np.int32)
            mask_tri = np.zeros((height, width), dtype=np.uint8)
            cv2.fillConvexPoly(mask_tri, tri_pts, 1)
            mask_tri = np.logical_and(mask_tri == 1, valid_mask)
            if not np.any(mask_tri):
                continue
            mean_color = [int(np.mean(image_rgb[:, :, c][mask_tri])) for c in range(3)]
            rendered_count += 1
            canvas[mask_tri] = mean_color
        logger.info(f"Rendered {rendered_count} Delaunay triangles")
    
    elif mode == "voronoi":
        logger.info("Rendering Voronoi polygons")
        rendered_count = 0
        from scipy.spatial import Voronoi
        vor = geometry
        for i, region_idx in enumerate(vor.point_region):
            region = vor.regions[region_idx]
            if not region or -1 in region:
                continue  # skip open regions
            polygon = np.array([vor.vertices[v] for v in region], dtype=np.int32)
            mask_poly = np.zeros((height, width), dtype=np.uint8)
            cv2.fillPoly(mask_poly, [polygon], 1)
            mask_poly = np.logical_and(mask_poly == 1, valid_mask)
            if not np.any(mask_poly):
                continue
            mean_color = [int(np.mean(image_rgb[:, :, c][mask_poly])) for c in range(3)]
            canvas[mask_poly] = mean_color
            rendered_count += 1
        logger.info(f"Rendered {rendered_count} Voronoi polygons")
    
    elif mode == "rectangles":
        logger.info("Rendering grid rectangles")
        rendered_count = 0
        # Divide the image into a grid of rectangles, each colored by the mean color of its region
        total_points = len(points) - 4  # Subtract the 4 corner points
        grid_size = int(np.sqrt(total_points))
        rect_h = max(1, height // grid_size)
        rect_w = max(1, width // grid_size)
        logger.info(f"Grid size: {grid_size}x{grid_size}, rectangle size: {rect_w}x{rect_h}")
        for i in range(grid_size):
            for j in range(grid_size):
                y0 = i * rect_h
                y1 = min((i + 1) * rect_h, height)
                x0 = j * rect_w
                x1 = min((j + 1) * rect_w, width)
                region_mask = np.zeros((height, width), dtype=bool)
                region_mask[y0:y1, x0:x1] = True
                region_mask = np.logical_and(region_mask, valid_mask)
                if not np.any(region_mask):
                    continue
                mean_color = [int(np.mean(image_rgb[:, :, c][region_mask])) for c in range(3)]
                rendered_count += 1
                canvas[region_mask] = mean_color
        logger.info(f"Rendered {rendered_count} grid rectangles")
    else:
        logger.error(f"Unsupported geometry mode: {mode}")
        raise ValueError(f"Unsupported geometry mode: {mode}")
    
    logger.info(f"render_geometry() EXIT: Completed rendering for {mode}")
    return canvas


def generate_cascade_fill(image_rgb, valid_mask, image_shape, mode, total_points, save_step_frames=False, output_dir=None):
    """
    Generate cascading fill pattern using spatially-optimized non-overlapping shapes.
    Uses distance transform and adjacency-based placement for better space utilization.
    
    Args:
        image_rgb (np.ndarray): Source image in RGB format.
        valid_mask (np.ndarray): Boolean mask of valid pixels.
        image_shape (tuple): (height, width) of the image.
        mode (str): Geometry mode ('delaunay', 'voronoi', 'rectangles').
        total_points (int): Approximate number of shapes to generate.
        save_step_frames (bool): Save intermediate frames for animation.
        output_dir (str, optional): Directory to save step frames.
    
    Returns:
        np.ndarray: Rendered canvas in RGB format.
    """
    logger.info(f"generate_cascade_fill() ENTRY: mode={mode}, target_points={total_points}, save_frames={save_step_frames}")
    import cv2
    import numpy as np
    from pathlib import Path
    from scipy import ndimage
    
    height, width = image_shape
    canvas = np.zeros_like(image_rgb)
    occupied_mask = np.zeros((height, width), dtype=bool)
    
    # Start with larger shapes and progressively get smaller
    max_size = min(height, width) // 4
    min_size = max(8, min(height, width) // 60)
    logger.info(f"Shape size range: {min_size} to {max_size} pixels")
    
    shapes_placed = 0
    frame_counter = 0
    
    # Initialize priority areas (start with entire valid region)
    priority_regions = []
    
    # Exponential decay for shape sizes with more granular steps
    size_steps = np.logspace(0, -2, num=25)  # From 1.0 to ~0.01, more gradual
    logger.info(f"Processing {len(size_steps)} size steps")
    
    for step_idx, size_ratio in enumerate(size_steps):
        current_size = int(max_size * size_ratio)
        if current_size < min_size:
            logger.info(f"Reached minimum size {min_size}, stopping at step {step_idx}")
            break
            
        # Adjust attempts based on size - more attempts for smaller shapes
        base_attempts = max(2, total_points // 25)
        size_multiplier = 1 + (1 - size_ratio) * 2  # More attempts for smaller shapes
        attempts_per_size = int(base_attempts * size_multiplier)
        logger.info(f"Step {step_idx}: size={current_size}, attempts={attempts_per_size}")
        
        import time
        step_start_time = time.perf_counter()
        placement_attempts = 0
        max_placement_attempts = attempts_per_size * 3  # Allow more attempts to find good spots
        shapes_this_step = 0
        successful_placements = 0
        failed_overlaps = 0
        failed_invalid_shapes = 0
        
        while placement_attempts < max_placement_attempts and shapes_placed < total_points:
            placement_attempts += 1
            
            # Log progress every 50 attempts for debugging
            if placement_attempts % 50 == 0:
                elapsed = time.perf_counter() - step_start_time
                logger.info(f"Step {step_idx}: attempt {placement_attempts}/{max_placement_attempts}, "
                          f"placed {successful_placements} shapes, elapsed {elapsed:.1f}s")
            
            # Get available space mask
            available_mask = valid_mask & ~occupied_mask
            if not np.any(available_mask):
                logger.info("No available space remaining")
                break
                
            # Find optimal placement location using spatial prioritization
            placement_start = time.perf_counter()
            center_x, center_y = find_optimal_placement(
                available_mask, occupied_mask, current_size, mode, shapes_placed == 0
            )
            placement_time = time.perf_counter() - placement_start
            
            if center_x is None or center_y is None:
                continue
            
            # Generate shape based on mode with boundary constraints
            shape_start = time.perf_counter()
            shape_mask = generate_shape_mask(
                center_x, center_y, current_size, mode, image_shape, 
                available_mask, occupied_mask
            )
            shape_time = time.perf_counter() - shape_start
            
            # Check if shape is valid and doesn't overlap
            if shape_mask is None or not np.any(shape_mask):
                failed_invalid_shapes += 1
                continue
                
            # Ensure no overlap (double-check)
            if np.any(shape_mask & occupied_mask):
                failed_overlaps += 1
                continue
                
            # Calculate mean color for the shape
            try:
                mean_color = [int(np.mean(image_rgb[:, :, c][shape_mask])) for c in range(3)]
            except:
                continue  # Skip if color calculation fails
            
            # Apply shape to canvas
            canvas[shape_mask] = mean_color
            occupied_mask |= shape_mask
            shapes_placed += 1
            shapes_this_step += 1
            successful_placements += 1
            
            # Log milestone progress
            if shapes_placed % 10 == 0:
                elapsed = time.perf_counter() - step_start_time
                logger.info(f"Milestone: {shapes_placed} shapes placed, step {step_idx}, "
                          f"elapsed {elapsed:.1f}s, avg {elapsed/shapes_placed:.2f}s per shape")
            
            # Save step frame if requested
            if save_step_frames and output_dir and frame_counter % 10 == 0:
                frame_path = Path(output_dir) / f"cascade_step_{frame_counter:04d}_{mode}.png"
                cv2.imwrite(str(frame_path), cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
                logger.info(f"Saved frame: {frame_path}")
            
            frame_counter += 1
            
            # Reset placement attempts after successful placement
            placement_attempts = 0
        
        # Log step completion with detailed stats
        step_elapsed = time.perf_counter() - step_start_time
        logger.info(f"Step {step_idx} complete: placed {successful_placements} shapes (total: {shapes_placed}), "
                   f"failed overlaps: {failed_overlaps}, invalid shapes: {failed_invalid_shapes}, "
                   f"elapsed: {step_elapsed:.1f}s")
        
        if shapes_placed >= total_points:
            logger.info(f"Reached target of {total_points} shapes")
            break
    
    logger.info(f"generate_cascade_fill() EXIT: Placed {shapes_placed} shapes total")
    return canvas


def find_optimal_placement(available_mask, occupied_mask, shape_size, mode, is_first_shape):
    """
    Find optimal placement location using spatial prioritization strategies.
    
    Args:
        available_mask (np.ndarray): Boolean mask of available pixels.
        occupied_mask (np.ndarray): Boolean mask of occupied pixels.
        shape_size (int): Size of shape to place.
        mode (str): Geometry mode.
        is_first_shape (bool): Whether this is the first shape being placed.
    
    Returns:
        tuple: (center_x, center_y) or (None, None) if no suitable location found.
    """
    import cv2
    import numpy as np
    from scipy import ndimage
    
    if not np.any(available_mask):
        return None, None
    
    height, width = available_mask.shape
    
    if is_first_shape:
        # For first shape, prefer center regions
        logger.info("Finding center placement for first shape")
        y_center, x_center = height // 2, width // 2
        # Find nearest available point to center
        available_coords = np.argwhere(available_mask)
        if len(available_coords) == 0:
            return None, None
        distances = np.sum((available_coords - np.array([y_center, x_center])) ** 2, axis=1)
        best_idx = np.argmin(distances)
        center_y, center_x = available_coords[best_idx]
        return int(center_x), int(center_y)
    
    # Strategy 1: Distance transform - find areas far from occupied regions (for larger shapes)
    # Strategy 2: Edge proximity - find areas near occupied regions (for smaller shapes)
    
    import time
    dt_start = time.perf_counter()
    
    # Compute distance transform from occupied areas
    if np.any(occupied_mask):
        logger.debug(f"Computing distance transform for occupied areas")
        distance_from_occupied = ndimage.distance_transform_edt(~occupied_mask)
        distance_from_occupied = distance_from_occupied * available_mask.astype(float)
    else:
        distance_from_occupied = available_mask.astype(float)
    
    dt_time = time.perf_counter() - dt_start
    logger.debug(f"Distance transform computed in {dt_time:.3f}s")
    
    # Compute distance from edges of occupied regions (for adjacency-based placement)
    edge_start = time.perf_counter()
    if np.any(occupied_mask):
        # Find edges of occupied regions
        logger.debug(f"Computing edge detection for occupied regions")
        occupied_edges = cv2.Canny(occupied_mask.astype(np.uint8) * 255, 50, 150) > 0
        if np.any(occupied_edges):
            distance_from_edges = ndimage.distance_transform_edt(~occupied_edges)
            distance_from_edges = distance_from_edges * available_mask.astype(float)
        else:
            distance_from_edges = np.ones_like(available_mask, dtype=float) * available_mask
    else:
        distance_from_edges = np.ones_like(available_mask, dtype=float) * available_mask
    
    edge_time = time.perf_counter() - edge_start
    logger.debug(f"Edge detection computed in {edge_time:.3f}s")
    
    # Create a buffer zone around occupied areas to prevent shapes from being too close
    buffer_size = max(2, shape_size // 4)
    if np.any(occupied_mask):
        occupied_dilated = cv2.dilate(occupied_mask.astype(np.uint8), 
                                    np.ones((buffer_size, buffer_size), np.uint8), iterations=1)
        safe_zone = available_mask & ~occupied_dilated.astype(bool)
    else:
        safe_zone = available_mask
    
    if not np.any(safe_zone):
        safe_zone = available_mask  # Fallback if buffer is too restrictive
    
    # Combine strategies based on shape size
    # Larger shapes: prefer areas far from occupied regions
    # Smaller shapes: prefer areas near occupied regions (gap filling)
    priority_start = time.perf_counter()
    
    size_ratio = shape_size / (min(height, width) // 4)  # Normalize size
    
    if size_ratio > 0.5:  # Large shapes - prefer open areas
        logger.debug(f"Using distance-based strategy for large shape (ratio: {size_ratio:.3f})")
        priority_map = distance_from_occupied * safe_zone.astype(float)
        # Add slight bias toward center for large shapes
        y_coords, x_coords = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
        center_bias = 1.0 - (((y_coords - height/2)**2 + (x_coords - width/2)**2) / 
                           ((height/2)**2 + (width/2)**2)) * 0.3
        priority_map *= center_bias
    else:  # Small shapes - prefer gap filling near edges
        logger.debug(f"Using edge-proximity strategy for small shape (ratio: {size_ratio:.3f})")
        # Invert distance from edges so closer = higher priority
        max_edge_dist = np.max(distance_from_edges) if np.any(distance_from_edges) else 1
        inverted_edge_distance = (max_edge_dist - distance_from_edges + 1) * safe_zone.astype(float)
        priority_map = inverted_edge_distance
    
    priority_time = time.perf_counter() - priority_start
    logger.debug(f"Priority map calculation completed in {priority_time:.3f}s")
    
    # Find areas that can accommodate the shape size
    placement_start = time.perf_counter()
    shape_buffer = shape_size // 2 + 2  # Add small buffer
    
    # OPTIMIZATION: Use spatial sampling instead of checking every pixel
    # For high-resolution images, checking every pixel is computationally prohibitive
    max_dimension = max(height, width)
    if max_dimension > 1000:  # High resolution
        sample_step = max(8, max_dimension // 100)  # Very aggressive sampling
    elif max_dimension > 500:  # Medium resolution
        sample_step = max(4, max_dimension // 150)  # Moderate sampling
    else:  # Low resolution
        sample_step = max(2, max_dimension // 200)  # Light sampling
    
    logger.info(f"Using optimized sampling: step={sample_step} for {height}x{width} image (max_dim={max_dimension})")
    
    valid_placement_mask = np.zeros_like(available_mask, dtype=bool)
    placement_checks = 0
    
    # Sample points at regular intervals instead of checking every pixel
    y_samples = range(shape_buffer, height - shape_buffer, sample_step)
    x_samples = range(shape_buffer, width - shape_buffer, sample_step)
    
    for y in y_samples:
        for x in x_samples:
            placement_checks += 1
            # Check if there's enough space around this point
            local_region = safe_zone[y-shape_buffer:y+shape_buffer+1, x-shape_buffer:x+shape_buffer+1]
            if np.sum(local_region) > (shape_buffer * 2 + 1) ** 2 * 0.6:  # At least 60% available
                # Mark a larger area around this valid point as available for aggressive sampling
                expansion = sample_step
                y_start, y_end = max(0, y-expansion), min(height, y+expansion+1)
                x_start, x_end = max(0, x-expansion), min(width, x+expansion+1)
                valid_placement_mask[y_start:y_end, x_start:x_end] = True
    
    placement_time = time.perf_counter() - placement_start
    potential_checks = (height-2*shape_buffer)*(width-2*shape_buffer)
    reduction_ratio = placement_checks / max(potential_checks, 1)
    logger.info(f"OPTIMIZATION: Placement validation completed in {placement_time:.3f}s with {placement_checks} checks (reduced from {potential_checks} potential checks, {reduction_ratio:.1%} of original)")
    
    # Apply valid placement constraint
    constraint_start = time.perf_counter()
    priority_map *= valid_placement_mask.astype(float)
    
    valid_pixels = np.sum(priority_map > 0)
    constraint_time = time.perf_counter() - constraint_start
    logger.debug(f"Constraint application completed in {constraint_time:.3f}s, valid pixels: {valid_pixels}")
    
    if not np.any(priority_map > 0):
        # Fallback: just find any available space
        logger.warning("No valid placements found, using fallback strategy")
        available_coords = np.argwhere(safe_zone)
        if len(available_coords) == 0:
            available_coords = np.argwhere(available_mask)
        if len(available_coords) == 0:
            return None, None
        
        # Select randomly from available coordinates
        idx = np.random.choice(len(available_coords))
        center_y, center_x = available_coords[idx]
        logger.debug(f"Fallback placement selected: ({center_x}, {center_y})")
        return int(center_x), int(center_y)
    
    # Find the best locations (top percentile)
    selection_start = time.perf_counter()
    flat_priorities = priority_map.flatten()
    threshold = np.percentile(flat_priorities[flat_priorities > 0], 85)  # Top 15% of locations
    
    best_locations = np.argwhere(priority_map >= threshold)
    
    if len(best_locations) == 0:
        # Fallback to any positive priority location
        best_locations = np.argwhere(priority_map > 0)
    
    if len(best_locations) == 0:
        return None, None
    
    # Select from best locations with some randomness
    selected_idx = np.random.choice(len(best_locations))
    center_y, center_x = best_locations[selected_idx]
    
    selection_time = time.perf_counter() - selection_start
    logger.debug(f"Final selection completed in {selection_time:.3f}s from {len(best_locations)} candidates")
    logger.debug(f"Selected placement: ({center_x}, {center_y})")
    
    return int(center_x), int(center_y)


def generate_shape_mask(center_x, center_y, size, mode, image_shape, available_mask=None, occupied_mask=None):
    """
    Generate a spatially-aware shape mask based on the specified geometry mode.
    
    Args:
        center_x (int): X coordinate of shape center.
        center_y (int): Y coordinate of shape center.
        size (int): Approximate size of the shape.
        mode (str): Geometry mode ('delaunay', 'voronoi', 'rectangles').
        image_shape (tuple): (height, width) of the image.
        available_mask (np.ndarray, optional): Boolean mask of available pixels.
        occupied_mask (np.ndarray, optional): Boolean mask of occupied pixels.
    
    Returns:
        np.ndarray: Boolean mask of the shape, or None if generation fails.
    """
    import cv2
    import numpy as np
    from scipy.spatial import Delaunay
    
    height, width = image_shape
    mask = np.zeros((height, width), dtype=bool)
    
    # Ensure center point is within bounds
    center_x = np.clip(center_x, 0, width - 1)
    center_y = np.clip(center_y, 0, height - 1)
    
    # Adaptive size based on available space
    if available_mask is not None:
        # Check local area to adapt size
        search_radius = min(size, min(height, width) // 4)
        y_min = max(0, center_y - search_radius)
        y_max = min(height, center_y + search_radius + 1)
        x_min = max(0, center_x - search_radius)
        x_max = min(width, center_x + search_radius + 1)
        
        local_available = available_mask[y_min:y_max, x_min:x_max]
        if np.any(local_available):
            available_ratio = np.sum(local_available) / local_available.size
            # Reduce size if area is constrained
            if available_ratio < 0.5:
                size = int(size * (available_ratio + 0.3))
    
    # Minimum size check
    size = max(size, 4)
    
    if mode == "rectangles":
        # Generate adaptive rectangular shapes with independent width/height
        # Use independent random dimensions for more artistic variation
        rect_width = int(size * np.random.uniform(0.5, 2.0))
        rect_height = int(size * np.random.uniform(0.5, 2.0))
        
        # Ensure minimum size
        rect_width = max(rect_width, 4)
        rect_height = max(rect_height, 4)
        
        half_width = rect_width // 2
        half_height = rect_height // 2
        
        # Add slight rotation for more organic feel
        angle = np.random.uniform(-15, 15)  # Small rotation in degrees
        
        if abs(angle) > 2:  # Apply rotation if significant
            # Create rotated rectangle with independent dimensions
            box_points = np.array([
                [-half_width, -half_height],
                [half_width, -half_height],
                [half_width, half_height],
                [-half_width, half_height]
            ], dtype=np.float32)
            
            # Rotation matrix
            angle_rad = np.radians(angle)
            cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
            rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            
            # Apply rotation and translation
            rotated_points = np.dot(box_points, rotation_matrix.T)
            rotated_points[:, 0] += center_x
            rotated_points[:, 1] += center_y
            rotated_points = rotated_points.astype(np.int32)
            
            # Clamp points to stay within image bounds
            rotated_points[:, 0] = np.clip(rotated_points[:, 0], 0, width - 1)
            rotated_points[:, 1] = np.clip(rotated_points[:, 1], 0, height - 1)
            
            temp_mask = np.zeros((height, width), dtype=np.uint8)
            cv2.fillPoly(temp_mask, [rotated_points], 1)
            mask = temp_mask.astype(bool)
        else:
            # Simple axis-aligned rectangle with independent dimensions
            # Calculate bounds centered on (center_x, center_y)
            x0 = center_x - half_width
            x1 = center_x + half_width
            y0 = center_y - half_height
            y1 = center_y + half_height
            
            # Clamp to image bounds while maintaining centering as much as possible
            x0 = max(0, x0)
            x1 = min(width, x1)
            y0 = max(0, y0)
            y1 = min(height, y1)
            
            # If clamping moved us off-center, try to rebalance
            if x0 == 0 and x1 < width:
                # Shift right if possible
                shift_right = min(width - x1, center_x - half_width)
                if shift_right > 0:
                    x1 = min(width, x1 + shift_right)
            elif x1 == width and x0 > 0:
                # Shift left if possible
                shift_left = min(x0, (center_x + half_width) - width)
                if shift_left > 0:
                    x0 = max(0, x0 - shift_left)
            
            if y0 == 0 and y1 < height:
                # Shift down if possible
                shift_down = min(height - y1, center_y - half_height)
                if shift_down > 0:
                    y1 = min(height, y1 + shift_down)
            elif y1 == height and y0 > 0:
                # Shift up if possible
                shift_up = min(y0, (center_y + half_height) - height)
                if shift_up > 0:
                    y0 = max(0, y0 - shift_up)
            
            # Ensure we have valid bounds
            if x1 > x0 and y1 > y0:
                mask[y0:y1, x0:x1] = True
        
    elif mode == "delaunay":
        # Generate triangular shapes using constrained Delaunay triangulation
        num_points = np.random.randint(3, 6)  # 3-5 points for triangulation
        
        # Create points with better distribution
        if occupied_mask is not None and np.any(occupied_mask):
            # Try to create shapes that fit well with existing geometry
            angles = np.random.uniform(0, 2*np.pi, num_points)
            # Vary radii more to create interesting shapes
            base_radii = np.random.uniform(size//4, size, num_points)
            
            # Add some angular variation for more organic shapes
            for i in range(len(angles)):
                if i > 0:
                    # Avoid too-similar angles
                    min_angle_diff = np.pi / 4
                    while any(abs(angles[i] - angles[j]) < min_angle_diff for j in range(i)):
                        angles[i] = np.random.uniform(0, 2*np.pi)
            
            radii = base_radii
        else:
            # First shape or no constraints - use regular distribution
            angles = np.linspace(0, 2*np.pi, num_points, endpoint=False)
            angles += np.random.uniform(0, 2*np.pi/num_points)  # Add random offset
            radii = np.random.uniform(size//3, size, num_points)
        
        points = []
        for angle, radius in zip(angles, radii):
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            x = np.clip(int(x), 0, width - 1)
            y = np.clip(int(y), 0, height - 1)
            points.append([x, y])
        
        # Remove duplicate points
        points = np.array(points)
        unique_points = []
        for point in points:
            if not any(np.allclose(point, existing, atol=1) for existing in unique_points):
                unique_points.append(point)
        
        if len(unique_points) >= 3:
            points = np.array(unique_points)
            try:
                tri = Delaunay(points)
                temp_mask = np.zeros((height, width), dtype=np.uint8)
                for simplex in tri.simplices:
                    triangle_pts = points[simplex].astype(np.int32)
                    cv2.fillConvexPoly(temp_mask, triangle_pts, 1)
                mask = temp_mask.astype(bool)
            except Exception:
                # Fallback to convex hull if triangulation fails
                try:
                    hull_points = cv2.convexHull(points.astype(np.int32))
                    temp_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.fillPoly(temp_mask, [hull_points], 1)
                    mask = temp_mask.astype(bool)
                except Exception:
                    # Final fallback to circle
                    temp_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.circle(temp_mask, (center_x, center_y), size//2, 1, -1)
                    mask = temp_mask.astype(bool)
    
    elif mode == "voronoi":
        # Generate organic polygon shapes (enhanced Voronoi-like cells)
        num_vertices = np.random.randint(4, 9)  # 4-8 vertices for variety
        
        # Create more natural, organic shapes
        base_angles = np.linspace(0, 2*np.pi, num_vertices, endpoint=False)
        # Add angular noise for organic feel
        angle_noise = np.random.normal(0, np.pi/8, num_vertices)
        angles = base_angles + angle_noise
        angles = np.sort(angles % (2*np.pi))  # Keep in [0, 2π] and sort
        
        # Variable radii with smooth transitions
        base_radius = size * 0.7
        radius_variation = size * 0.3
        radii = []
        
        for i, angle in enumerate(angles):
            # Create smooth radius variation using sine waves
            variation = np.sin(angle * 3) * 0.3 + np.sin(angle * 7) * 0.1
            radius = base_radius + radius_variation * variation
            # Add some random noise
            radius += np.random.uniform(-size*0.1, size*0.1)
            radius = max(size//4, radius)  # Minimum radius
            radii.append(radius)
        
        points = []
        for angle, radius in zip(angles, radii):
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            x = np.clip(int(x), 0, width - 1)
            y = np.clip(int(y), 0, height - 1)
            points.append([x, y])
        
        if len(points) >= 3:
            polygon = np.array(points, dtype=np.int32)
            temp_mask = np.zeros((height, width), dtype=np.uint8)
            cv2.fillPoly(temp_mask, [polygon], 1)
            mask = temp_mask.astype(bool)
    
    # Final validation - ensure shape is within available area
    if available_mask is not None:
        mask = mask & available_mask
    
    # Check if the generated shape is valid (has some area)
    if not np.any(mask):
        return None
    
    # Ensure minimum shape size
    shape_area = np.sum(mask)
    if shape_area < 4:  # At least 4 pixels
        return None
    
    return mask
