"""
Cubist Art Generator Core Logic

__version__ = "v12d"
__author__ = "Corey Prator"
__date__ = "2025-07-27"
"""

# Import logging
from cubist_logger import logger
from typing import List, Dict, Tuple, Optional

def sample_points_deterministic(img, total_points, seed):
    """
    Deterministically sample points from the valid region of img using the given seed.
    Returns an (N,2) array of (x, y) points.
    """
    import numpy as np
    rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()
    height, width = img.shape[:2]
    valid_mask = np.ones((height, width), dtype=bool)
    valid_coords = np.argwhere(valid_mask)
    if len(valid_coords) < 4:
        raise ValueError("Not enough valid pixels to sample points.")
    idxs = rng.choice(valid_coords.shape[0], min(total_points, len(valid_coords)), replace=False)
    sampled_points = valid_coords[idxs][:, [1, 0]]  # (x, y)
    return sampled_points

def run_cubist(input_path, output_dir, mask_path=None, total_points=1000, clip_to_alpha=True,
               verbose=True, geometry_mode="delaunay", use_cascade_fill=False, save_step_frames=False, seed: int = None):
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
    import random
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
        mask_alpha = np.where(mask == 255, 255, 0).astype(np.uint8)
        logger.info(f"Using mask with {np.sum(valid_mask)} valid pixels for placement, {np.sum(mask_alpha == 255)} pixels will be opaque")
    else:
        valid_mask = (alpha > 0)
        mask_alpha = None
        logger.info(f"No mask provided, using alpha channel with {np.sum(valid_mask)} valid pixels")

    # Use a local RNG for all random choices
    rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)

    # --- Deterministic point sampling ---
    def _sample_points(valid_mask, total_points, seed):
        valid_coords = np.argwhere(valid_mask)
        if len(valid_coords) < 4:
            logger.error("Not enough valid pixels to sample points")
            raise ValueError("Not enough valid pixels to sample points.")
        rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()
        idxs = rng.choice(valid_coords.shape[0], min(total_points, len(valid_coords)), replace=False)
        sampled_points = valid_coords[idxs][:, [1, 0]]  # (x, y)
        return sampled_points

    requested_points = total_points
    sampled_points = _sample_points(valid_mask, total_points, seed)
    pts = sampled_points.copy()
    corners_added = 0
    if geometry_mode in ("delaunay", "voronoi"):
        corners = np.array([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]])
        pts = np.vstack([pts, corners])
        corners_added = 4
    logger.info(f"Points: requested={requested_points}, sampled={len(sampled_points)}, corners_added={corners_added}, total_after_corners={len(pts)}")

    # --- Cascade fill logic ---
    if use_cascade_fill:
        # Use the same sampled points for all cascade stages
        cascade_metrics = []
        # For demonstration, let's say cascade has 3 stages (could be parameterized)
        n_stages = 3
        stage_points = np.array_split(pts, n_stages)
        canvas = np.zeros_like(image_rgb)
        all_shapes = []
        for i, stage_pts in enumerate(stage_points):
            logger.info(f"Cascade stage {i+1}/{n_stages}: {len(stage_pts)} points")
            geometry = generate_geometry(stage_pts, (height, width), geometry_mode, use_cascade_fill=False)
            canvas_stage, shapes = render_geometry(
                image_rgb, valid_mask, geometry, stage_pts, geometry_mode,
                shapes_accumulator=None
            )
            all_shapes.extend(shapes)
            # Optionally blend canvas_stage into canvas, or just keep last
            canvas = canvas_stage
            cascade_metrics.append({
                "stage": i+1,
                "points": len(stage_pts),
                "shapes": len(shapes)
            })
        shapes = all_shapes
        metrics_dict = {
            "cascade_stages": cascade_metrics,
            "total_shapes": len(all_shapes),
            "total_points": len(pts),
            "requested_points": requested_points,
            "corners_added": corners_added,
        }
    else:
        # Use regular tessellation approach
        logger.info("Using regular tessellation approach")
        geometry = generate_geometry(pts, (height, width), geometry_mode, use_cascade_fill=False)
        shapes: list[dict] = []
        canvas, shapes = render_geometry(
            image_rgb, valid_mask, geometry, pts, geometry_mode,
            shapes_accumulator=None
        )
        metrics_dict = {
            "cascade_stages": None,
            "total_shapes": len(shapes),
            "total_points": len(pts),
            "requested_points": requested_points,
            "corners_added": corners_added,
        }

    # Apply proper alpha channel based on mask
    if mask_path is not None:
        mask_name = Path(mask_path).stem.lower()
        if "edge_density" in mask_name:
            logger.info("Edge density mask - using original alpha channel")
            # For edge density masks: don't modify transparency, just use for sampling
            final_alpha = alpha
        else:
            logger.info("Regular mask - applying mask-based transparency")
            # Use mask-based alpha: white areas = opaque, non-white = transparent
            final_alpha = mask_alpha
            logger.info(f"Applied mask-based transparency: {np.sum(final_alpha == 255)} opaque pixels")
    else:
        # Use original alpha channel
        final_alpha = alpha
    
    # Create RGBA output
    canvas_rgba = np.dstack((canvas, final_alpha))
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Update output filename to include cascade flag and mask status
    cascade_flag = "cascade" if use_cascade_fill else "regular"
    mask_flag = ""
    if mask_path is not None:
        mask_name = Path(mask_path).stem.lower()
        if "edge_density" in mask_name:
            mask_flag = "_edge_density_mask"
        else:
            mask_flag = "_masked"

    # Check if this is a background image and add prefix
    bg_prefix = "bg_" if "bg_" in str(input_path).lower() else ""
    
    output_name = f"{bg_prefix}your_input_image_{total_points:05d}pts_{geometry_mode}_{cascade_flag}{mask_flag}_{timestamp}.png"
    output_path = Path(output_dir) / output_name
    logger.info(f"Saving output to: {output_path}")
    cv2.imwrite(str(output_path), cv2.cvtColor(canvas_rgba, cv2.COLOR_RGBA2BGRA))
    if verbose:
        print(f"Saved: {os.path.abspath(str(output_path))}")
    logger.info(f"run_cubist() EXIT: Successfully saved {output_path}")
    final_png_path = output_path  # or whatever variable holds the PNG path
    # Save PNG as before...
    # SVG export (when a path was supplied)
    # (SVG writing is now handled in cubist_cli.py, not here)
    # Emit a METRICS line for the validator
    metrics = {
        "geometry": geometry_mode,
        "requested_points": int(requested_points),
        "total_points_after_corners": int(len(pts)),
        "shape_count": int(len(shapes)),
    }
    print(f"METRICS: {metrics}")
    return output_path, shapes, (width, height), sampled_points, metrics_dict


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


def render_geometry(image_rgb, valid_mask, geometry, pts, mode, shapes_accumulator=None):
    """
    Render geometry shapes onto a canvas using the original tessellation approach.
    
    Args:
        image_rgb (np.ndarray): Source image in RGB format.
        valid_mask (np.ndarray): Boolean mask of valid pixels.
        geometry: Geometry object from generate_geometry().
        pts (np.ndarray): Array of (x, y) points.
        mode (str): Geometry mode ('delaunay', 'voronoi', 'rectangles').
    
    Returns:
        np.ndarray: Rendered canvas in RGB format.
    """
    logger.info(f"render_geometry() ENTRY: mode={mode}")
    import cv2
    import numpy as np
    
    height, width = image_rgb.shape[:2]
    canvas = np.zeros_like(image_rgb)
    shapes = []
    if mode == "delaunay":
        logger.info(f"Rendering Delaunay triangles: {len(geometry.simplices)} triangles")
        rendered_count = 0
        for simplex in geometry.simplices:
            tri_pts = pts[simplex].astype(np.int32)
            tri_pts = np.clip(tri_pts, 0, np.array([width-1, height-1])).reshape(-1, 2)
            mask_tri = np.zeros((height, width), dtype=np.uint8)
            cv2.fillConvexPoly(mask_tri, tri_pts, 1)
            mask_tri = np.logical_and(mask_tri == 1, valid_mask)
            if not np.any(mask_tri):
                continue
            mean_color = [int(np.mean(image_rgb[:, :, c][mask_tri])) for c in range(3)]
            rendered_count += 1
            canvas[mask_tri] = mean_color
            # Add to shapes
            shapes.append({
                "type": "polygon",
                "points": [(int(tri_pts[0][0]), int(tri_pts[0][1])),
                           (int(tri_pts[1][0]), int(tri_pts[1][1])),
                           (int(tri_pts[2][0]), int(tri_pts[2][1]))],
                "fill": tuple(mean_color)
            })
            if shapes_accumulator is not None:
                shapes_accumulator.append({
                    "type": "polygon",
                    "points": [(int(tri_pts[0][0]), int(tri_pts[0][1])),
                               (int(tri_pts[1][0]), int(tri_pts[1][1])),
                               (int(tri_pts[2][0]), int(tri_pts[2][1]))],
                    "fill": "none",
                    "stroke": "#000000",
                    "stroke_width": 1,
                })
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
            # Add to shapes
            shapes.append({
                "type": "polygon",
                "points": [(int(px), int(py)) for (px, py) in polygon],
                "fill": tuple(mean_color)
            })
            if shapes_accumulator is not None:
                shapes_accumulator.append({
                    "type": "polygon",
                    "points": [(int(px), int(py)) for (px, py) in polygon],
                    "fill": "none",
                    "stroke": "#000000",
                    "stroke_width": 1,
                })
        logger.info(f"Rendered {rendered_count} Voronoi polygons")
    elif mode == "rectangles":
        logger.info("Rendering grid rectangles")
        rendered_count = 0
        total_points = max(0, len(pts) - 4)  # Subtract the 4 corner points
        grid_size = max(1, int(np.sqrt(total_points)))
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
                # Add to shapes
                shapes.append({
                    "type": "rect",
                    "x": int(x0), "y": int(y0),
                    "w": int(x1 - x0), "h": int(y1 - y0),
                    "fill": tuple(mean_color)
                })
                if shapes_accumulator is not None:
                    w = int(x1 - x0)
                    h = int(y1 - y0)
                    shapes_accumulator.append({
                        "type": "rect",
                        "x": int(x0), "y": int(y0),
                        "w": w,  "h": h,
                        "fill": "#ffffff",
                        "stroke": "#000000",
                        "stroke_width": 1,
                    })
        logger.info(f"Rendered {rendered_count} grid rectangles")
    else:
        logger.error(f"Unsupported geometry mode: {mode}")
        raise ValueError(f"Unsupported geometry mode: {mode}")
    logger.info(f"render_geometry() EXIT: Completed rendering for {mode}")
    return canvas, shapes


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
    # Randomly select one of the best locations
    idx = np.random.choice(len(best_locations))
    center_y, center_x = best_locations[idx]
    
    selection_time = time.perf_counter() - selection_start
    logger.info(f"Optimal placement found: ({center_x}, {center_y}), selection time: {selection_time:.3f}s")
    
    return int(center_x), int(center_y)


def generate_shape_mask(center_x, center_y, size, mode, image_shape, available_mask, occupied_mask):
    """
    Generate a mask for the shape to be placed, based on the desired geometry mode.
    
    Args:
        center_x (int): X-coordinate of the shape center.
        center_y (int): Y-coordinate of the shape center.
        size (int): Size of the shape.
        mode (str): Geometry mode ('delaunay', 'voronoi', 'rectangles').
        image_shape (tuple): (height, width) of the image.
        available_mask (np.ndarray): Boolean mask of available pixels.
        occupied_mask (np.ndarray): Boolean mask of occupied pixels.
    
    Returns:
        np.ndarray: Boolean mask of the shape area, or None if shape could not be generated.
    """
    import cv2
    import numpy as np
    
    height, width = image_shape
    
    if mode == "delaunay":
        logger.info(f"Generating Delaunay mask at ({center_x}, {center_y}), size {size}")
        # For Delaunay, generate a triangle around the center point
        # Randomly perturb the triangle vertices for variability
        perturb = size // 4
        pts = np.array([
            [center_x, center_y - size],
            [center_x - size + np.random.randint(-perturb, perturb), center_y + size],
            [center_x + size - np.random.randint(-perturb, perturb), center_y + size]
        ], dtype=np.int32)
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillConvexPoly(mask, pts, 1)
        # Safety: mask is uint8, convert to bool for logic
        mask = mask.astype(bool)
        # Ensure the mask is valid
        if np.sum(mask) < 10:
            logger.warning("Generated Delaunay mask is too small, skipping")
            return None
        return mask
    elif mode == "voronoi":
        logger.info(f"Generating Voronoi mask at ({center_x}, {center_y}), size {size}")
        # For Voronoi, generate a polygonal region around the center point
        num_vertices = np.random.randint(3, 8)
        angle_steps = np.linspace(0, 2 * np.pi, num_vertices, endpoint=False) + np.random.uniform(0, 2 * np.pi / num_vertices)
        radius = size * np.random.uniform(0.5, 1.0, num_vertices)
        pts = np.array([[center_x + int(r * np.cos(a)), center_y + int(r * np.sin(a))] for r, a in zip(radius, angle_steps)], dtype=np.int32)
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, [pts], 1)
        # Safety: mask is uint8, convert to bool for logic
        mask = mask.astype(bool)
        # Ensure the mask is valid
        if np.sum(mask) < 10:
            logger.warning("Generated Voronoi mask is too small, skipping")
            return None
        return mask
    elif mode == "rectangles":
        logger.info(f"Generating rectangular mask at ({center_x}, {center_y}), size {size}")
        # For rectangles, just use a square around the center
        half_size = size // 2
        x0 = max(center_x - half_size, 0)
        x1 = min(center_x + half_size, width)
        y0 = max(center_y - half_size, 0)
        y1 = min(center_y + half_size, height)
        mask = np.zeros((height, width), dtype=bool)
        mask[y0:y1, x0:x1] = True
        # Ensure the mask is valid
        if np.sum(mask) < 10:
            logger.warning("Generated rectangular mask is too small, skipping")
            return None
        return mask
    else:
        logger.error(f"Unsupported geometry mode for mask generation: {mode}")
        return None

# Ensure all OpenCV drawing calls use uint8, not bool
def safe_fillConvexPoly(img, pts, color, *args, **kwargs):
    if img.dtype == np.bool_:
        logging.debug("Converting mask to uint8 for OpenCV draw (fillConvexPoly)")
        img = img.astype(np.uint8) * 255
    return cv2.fillConvexPoly(img, pts, color, *args, **kwargs)

def safe_rectangle(img, pt1, pt2, color, *args, **kwargs):
    if img.dtype == np.bool_:
        logging.debug("Converting mask to uint8 for OpenCV draw (rectangle)")
        img = img.astype(np.uint8) * 255
    return cv2.rectangle(img, pt1, pt2, color, *args, **kwargs)

def safe_circle(img, center, radius, color, *args, **kwargs):
    if img.dtype == np.bool_:
        logging.debug("Converting mask to uint8 for OpenCV draw (circle)")
        img = img.astype(np.uint8) * 255
    return cv2.circle(img, center, radius, color, *args, **kwargs)

def safe_polylines(img, pts, isClosed, color, *args, **kwargs):
    if img.dtype == np.bool_:
        logging.debug("Converting mask to uint8 for OpenCV draw (polylines)")
        img = img.astype(np.uint8) * 255
    return cv2.polylines(img, pts, isClosed, color, *args, **kwargs)

def safe_drawContours(img, contours, contourIdx, color, *args, **kwargs):
    if img.dtype == np.bool_:
        logging.debug("Converting mask to uint8 for OpenCV draw (drawContours)")
        img = img.astype(np.uint8) * 255
    return cv2.drawContours(img, contours, contourIdx, color, *args, **kwargs)

# Utility: ensure mask/canvas is uint8 for OpenCV
def ensure_uint8_mask(mask, logger=None):
    if mask.dtype == np.bool_:
        if logger:
            logger.debug("Converting mask/canvas to uint8 for OpenCV")
        return (mask.astype(np.uint8) * 255)
    return mask

# Patch all uses in cascade fill and shape rasterization
# Example: in generate_cascade_fill or similar, replace cv2.fillConvexPoly(mask, ...) with cv2.fillConvexPoly(ensure_uint8_mask(mask, logger), ...)
# If you find mask = np.zeros(...) with dtype=bool, change to dtype=np.uint8
# If you find mask = np.zeros(...) with dtype=bool, change to dtype=np.uint8
