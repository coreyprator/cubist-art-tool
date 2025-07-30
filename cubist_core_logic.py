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

def run_cubist(input_path, output_dir, mask_path=None, total_points=1000, clip_to_alpha=True, verbose=True):
    import cv2
    import numpy as np
    from scipy.spatial import Delaunay
    from pathlib import Path
    import os

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load input image (with alpha)
    image_bgra = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
    if image_bgra is None:
        raise FileNotFoundError(f"Input image not found: {input_path}")
    if image_bgra.shape[2] == 4:
        image_rgb = cv2.cvtColor(image_bgra[:, :, :3], cv2.COLOR_BGR2RGB)
        alpha = image_bgra[:, :, 3]
    else:
        image_rgb = cv2.cvtColor(image_bgra, cv2.COLOR_BGR2RGB)
        alpha = np.ones(image_rgb.shape[:2], dtype=np.uint8) * 255
    height, width = image_rgb.shape[:2]

    # Load mask if provided
    if mask_path is not None:
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if mask is None or mask.shape != (height, width):
            raise ValueError(f"Mask not found or size mismatch: {mask_path}")
        valid_mask = (mask > 0) & (alpha > 0)
    else:
        valid_mask = (alpha > 0)

    # Sample points from valid region
    valid_coords = np.argwhere(valid_mask)
    if len(valid_coords) < 4:
        raise ValueError("Not enough valid pixels to sample points.")
    idxs = np.random.choice(valid_coords.shape[0], min(total_points, len(valid_coords)), replace=False)
    pts = valid_coords[idxs][:, [1, 0]]  # (x, y)

    # Add corners
    corners = np.array([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]])
    pts = np.vstack([pts, corners])

    # Delaunay triangulation
    tri = Delaunay(pts)

    # Render mesh
    canvas = np.zeros_like(image_rgb)
    for simplex in tri.simplices:
        tri_pts = pts[simplex].astype(np.int32)
        mask_tri = np.zeros((height, width), dtype=np.uint8)
        cv2.fillConvexPoly(mask_tri, tri_pts, 1)
        # Only keep pixels in valid region
        mask_tri = np.logical_and(mask_tri == 1, valid_mask)
        if not np.any(mask_tri):
            continue
        mean_color = [int(np.mean(image_rgb[:, :, c][mask_tri])) for c in range(3)]
        canvas[mask_tri] = mean_color

    # Preserve alpha in output
    canvas_rgba = np.dstack((canvas, alpha))
    output_name = f"your_input_image_{total_points:05d}pts.png"
    output_path = Path(output_dir) / output_name
    cv2.imwrite(str(output_path), cv2.cvtColor(canvas_rgba, cv2.COLOR_RGBA2BGRA))
    if verbose:
        print(f"Saved: {os.path.abspath(str(output_path))}")
    return str(output_path)
