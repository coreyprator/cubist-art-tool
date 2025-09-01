# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: archive/cubist_mixedgeo_inpaint_v2.py.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:23:59+02:00
# === CUBIST STAMP END ===

import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay, Voronoi
import time
import os
import json
from datetime import datetime, timedelta


# Print current working directory and program start time
program_start = datetime.now()
cwd = os.getcwd()
print(f"[START {program_start.strftime('%H:%M:%S')}] Program started.")
print(f"Current working directory: {cwd}")

# === Triangle alpha clipping flag ===
CLIP_TRIANGLES_TO_ALPHA = True  # If True, triangles are clipped to alpha>0; if False, triangles are skipped if any vertex is outside alpha>0


# INPUT_IMAGE = 'filled_bg_input_image.png'
INPUT_IMAGE = "statue_input_image.png"  # Change this to your input image file path

# === Edge Visualization Section ===
# Load image (with transparency if present) and convert to grayscale
image_vis = cv2.imread(INPUT_IMAGE, cv2.IMREAD_UNCHANGED)
if image_vis.shape[2] == 4:
    rgb_vis = cv2.cvtColor(image_vis[:, :, :3], cv2.COLOR_BGR2RGB)
    alpha_vis = image_vis[:, :, 3]
    gray_vis = cv2.cvtColor(image_vis[:, :, :3], cv2.COLOR_BGR2GRAY)
else:
    rgb_vis = cv2.cvtColor(image_vis, cv2.COLOR_BGR2RGB)
    alpha_vis = None
    gray_vis = cv2.cvtColor(image_vis, cv2.COLOR_BGR2GRAY)

# Detect edges
edges_vis = cv2.Canny(gray_vis, threshold1=100, threshold2=200)

# Save binary edge map
cv2.imwrite("edges_gray.png", edges_vis)

# Create red overlay on original image
overlay_vis = rgb_vis.copy()
overlay_vis[edges_vis > 0] = [255, 0, 0]  # Red where edges

# Save overlay image
cv2.imwrite("edge_overlay.png", cv2.cvtColor(overlay_vis, cv2.COLOR_RGB2BGR))

# === Config ===

TOTAL_POINTS = 1000
NUM_FRAMES = 20
GROWTH_FACTOR = 1.53
EDGE_FRACTION = 0.2
SAVE_POINTS = True
LOAD_EXISTING_POINTS = False
POINTS_FILE = "point_data.json"
USE_MIXED_GEOMETRY = True  # New flag for mixed geometry rendering

# === Frame Control Settings ===
single_frame_mode = (
    True  # Set to True to render only one frame at a specific point count
)
point_target = 10000  # Used if single_frame_mode is True
num_frames = 20  # Total number of frames if single_frame_mode is False
base_point = 2  # Starting number of points for geometric progression
factor = GROWTH_FACTOR  # Growth factor for geometric progression

# === Load and split image (for triangulation) ===
image_bgra = cv2.imread(INPUT_IMAGE, cv2.IMREAD_UNCHANGED)
if image_bgra.shape[2] == 4:
    image_rgb = cv2.cvtColor(image_bgra[:, :, :3], cv2.COLOR_BGR2RGB)
    alpha = image_bgra[:, :, 3]
else:
    image_rgb = cv2.cvtColor(image_bgra, cv2.COLOR_BGR2RGB)
    alpha = (
        np.ones(image_rgb.shape[:2], dtype=np.uint8) * 255
    )  # No alpha, treat as fully opaque

height, width = image_rgb.shape[:2]


def generate_edge_mask_biased_points(
    image,
    total_points=5000,
    edge_fraction=0.2,
    mask_path="edge_mask.png",
    alpha_mask=None,
):
    height, width = image.shape[:2]
    num_edge_points = int(total_points * edge_fraction)
    num_random_points = total_points - num_edge_points

    # Load edge mask (assume black pixels are edges)
    edge_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if edge_mask is None or edge_mask.shape != (height, width):
        raise ValueError(
            f"Edge mask '{mask_path}' not found or does not match image size."
        )

    # Find black pixels (value == 0) in the mask
    edge_coords = np.argwhere(edge_mask == 0)
    # Filter edge_coords by alpha if provided
    if alpha_mask is not None:
        edge_coords = np.array(
            [pt for pt in edge_coords if alpha_mask[pt[0], pt[1]] > 0]
        )
    if len(edge_coords) > 0:
        chosen_edge_points = edge_coords[
            np.random.choice(
                edge_coords.shape[0],
                min(num_edge_points, len(edge_coords)),
                replace=False,
            )
        ]
        # Convert from (row, col) to (x, y)
        chosen_edge_points = chosen_edge_points[:, [1, 0]]
    else:
        chosen_edge_points = np.empty((0, 2), dtype=np.int32)
    chosen_edge_points = np.array(chosen_edge_points).reshape(-1, 2)

    # Uniform random points for the rest, but only on non-transparent areas
    if alpha_mask is not None:
        valid_mask = np.argwhere(alpha_mask > 0)
        if len(valid_mask) > 0:
            idxs = np.random.choice(
                valid_mask.shape[0], num_random_points, replace=True
            )
            random_points = valid_mask[idxs][:, [1, 0]]
        else:
            random_points = np.empty((0, 2), dtype=np.int32)
    else:
        xs = np.random.randint(0, width, num_random_points)
        ys = np.random.randint(0, height, num_random_points)
        random_points = np.vstack((xs, ys)).T
    random_points = np.array(random_points).reshape(-1, 2)

    # Add corners (if not transparent)
    corners = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]]
    )
    if alpha_mask is not None:
        corners = np.array(
            [pt for pt in corners if alpha_mask[pt[1], pt[0]] > 0]
        ).reshape(-1, 2)
    else:
        corners = corners.reshape(-1, 2)

    all_points = np.vstack((chosen_edge_points, random_points, corners))
    return all_points


# === Check edge mask and input image size match ===
edge_mask_path = "edge_mask.png"
edge_mask_img = cv2.imread(edge_mask_path, cv2.IMREAD_GRAYSCALE)
if edge_mask_img is None:
    raise FileNotFoundError(f"Edge mask '{edge_mask_path}' not found.")
if edge_mask_img.shape[0] != height or edge_mask_img.shape[1] != width:
    raise ValueError(
        f"Image size mismatch: '{INPUT_IMAGE}' is {width}x{height}, but '{edge_mask_path}' is {edge_mask_img.shape[1]}x{edge_mask_img.shape[0]}."
    )

# === Prepare point set ===
if LOAD_EXISTING_POINTS and os.path.exists(POINTS_FILE):
    with open(POINTS_FILE, "r") as f:
        data = json.load(f)
        fixed_points = np.array(data["points"])
else:
    fixed_points = generate_edge_mask_biased_points(
        image_rgb,
        TOTAL_POINTS,
        EDGE_FRACTION,
        mask_path=edge_mask_path,
        alpha_mask=alpha,
    )
    if SAVE_POINTS:
        with open(POINTS_FILE, "w") as f:
            json.dump({"points": fixed_points.tolist()}, f)

# === Animation Frames ===
start_time = time.time()
prev_time = start_time
frame_times = []
points_history = []

if single_frame_mode:
    frame_indices = [1]
    point_counts = [point_target]
else:
    frame_indices = range(1, num_frames + 1)
    point_counts = [
        min(int(base_point * (factor ** (frame - 1))), TOTAL_POINTS)
        for frame in frame_indices
    ]


for idx, (frame, N) in enumerate(zip(frame_indices, point_counts), 1):
    # N is the number of points for this frame
    pts = fixed_points[:N]
    # Filter points by alpha (remove points on fully transparent areas)
    if alpha is not None:
        pts = np.array(
            [
                pt
                for pt in pts
                if (
                    0 <= int(pt[0]) < width
                    and 0 <= int(pt[1]) < height
                    and alpha[int(pt[1]), int(pt[0])] > 0
                )
            ]
        )
    points = np.vstack(
        [pts, [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]]]
    )

    # Start triangulation stopwatch
    checkpoint_time = time.time()
    # Print estimated time remaining for this frame (use previous frame_elapsed if available)
    est_time = frame_times[-1] if frame_times else 0
    print(f"Starting triangulation... estimated time remaining: ~{int(est_time)}s")

    tri = Delaunay(points)

    canvas = np.zeros_like(image_rgb)
    for simplex in tri.simplices:
        tri_pts = points[simplex].astype(np.int32)
        # Check if all triangle vertices are within bounds and non-transparent
        if CLIP_TRIANGLES_TO_ALPHA:
            # Always render, but mask to alpha > 0
            mask = np.zeros((height, width), dtype=np.uint8)
            cv2.fillConvexPoly(mask, tri_pts, 1)
            # Only keep pixels where alpha > 0
            mask = np.logical_and(mask == 1, alpha > 0)
            if not np.any(mask):
                continue
            mean_color = [int(np.mean(image_rgb[:, :, c][mask])) for c in range(3)]
            canvas[mask] = mean_color
        else:
            valid = True
            for pt in tri_pts:
                x, y = int(pt[0]), int(pt[1])
                if not (0 <= x < width and 0 <= y < height and alpha[y, x] > 0):
                    valid = False
                    break
            if not valid:
                continue
            mask = np.zeros((height, width), dtype=np.uint8)
            cv2.fillConvexPoly(mask, tri_pts, 1)
            mean_color = [int(np.mean(image_rgb[:, :, c][mask == 1])) for c in range(3)]
            canvas[mask == 1] = mean_color

    # === Mixed Geometry Rendering ===
    if USE_MIXED_GEOMETRY:
        # Compute Voronoi regions for points
        vor = Voronoi(points)
        for i, region_idx in enumerate(vor.point_region):
            region = vor.regions[region_idx]
            if -1 in region or len(region) == 0:
                continue  # skip open regions
            polygon = np.array([vor.vertices[v] for v in region], np.int32)
            mask = np.zeros((height, width), np.uint8)
            cv2.fillPoly(mask, [polygon], 1)
            region_pixels = image_rgb[mask == 1]
            if len(region_pixels) == 0:
                print(f"[DEBUG] Skipping region {i}: no pixels in mask.")
                continue
            mean_color = np.mean(region_pixels, axis=0)
            if (
                mean_color.shape[0] != 3
                or np.any(np.isnan(mean_color))
                or not np.all(np.isfinite(mean_color))
            ):
                print(f"[DEBUG] Skipping region {i}: invalid mean color {mean_color}.")
                continue
            color_std = np.std(region_pixels)
            color_tuple = tuple(int(x) for x in mean_color)
            if color_std < 20:  # Low variance: use rectangle or circle
                (x, y), radius = cv2.minEnclosingCircle(polygon)
                if radius < 5:
                    rect = cv2.boundingRect(polygon)
                    cv2.rectangle(
                        canvas,
                        (rect[0], rect[1]),
                        (rect[0] + rect[2], rect[1] + rect[3]),
                        color_tuple,
                        -1,
                    )
                else:
                    cv2.circle(canvas, (int(x), int(y)), int(radius), color_tuple, -1)
            else:  # High variance: use triangle
                cv2.fillPoly(canvas, [polygon], color_tuple)
    else:
        # ...existing triangle rendering code...
        pass

    # === Inpaint voids after all geometry is rendered ===
    void_mask = ((np.all(canvas == 0, axis=2)) & (alpha > 0)).astype(np.uint8)
    # Save void mask for debug
    void_mask_path = f"void_mask_{frame:02d}_{N:05d}pts.png"
    cv2.imwrite(void_mask_path, void_mask * 255)
    print(f"Saved: {os.path.abspath(void_mask_path)} (void mask)")
    # Dilate void mask to include edge areas
    kernel = np.ones((3, 3), np.uint8)
    void_mask_dilated = cv2.dilate(void_mask, kernel, iterations=1)
    # Inpaint expects 8-bit single or 3-channel, so convert canvas to BGR for inpainting
    if np.any(void_mask_dilated):
        canvas_bgr = cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR)
        inpainted = cv2.inpaint(canvas_bgr, void_mask_dilated, 3, cv2.INPAINT_TELEA)
        canvas = cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)
        # Check for remaining black after inpainting
        remaining_void = (np.all(canvas == 0, axis=2)) & (alpha > 0)
        if np.any(remaining_void):
            print(
                "[WARNING] Remaining black voids after inpainting. Applying fallback fill."
            )
            # Fill remaining voids with neutral color (e.g., mean of image_rgb where alpha > 0)
            neutral_color = tuple(int(x) for x in np.mean(image_rgb[alpha > 0], axis=0))
            for c in range(3):
                channel = canvas[:, :, c]
                channel[remaining_void] = neutral_color[c]
                canvas[:, :, c] = channel
            # Save fallback void mask for debug
            fallback_mask_path = f"void_mask_fallback_{frame:02d}_{N:05d}pts.png"
            cv2.imwrite(fallback_mask_path, remaining_void.astype(np.uint8) * 255)
            print(f"Saved: {os.path.abspath(fallback_mask_path)} (fallback void mask)")

    frame_name = f"frame_{frame:02d}_{N:05d}pts.png"
    combined_frame_name = f"frame_{frame:02d}_{N:05d}pts_with_edges.png"

    if image_bgra.shape[2] == 4:
        # Preserve alpha in output
        canvas_rgba = np.dstack((canvas, alpha))
        # Validate that canvas_rgba is not all black/zero
        if not np.any(canvas_rgba[:, :, :3]):
            print(
                f"[WARNING] canvas_rgba is all black/zero before saving {frame_name}!"
            )
        plt.figure(figsize=(width / 100, height / 100), dpi=100)
        plt.axis("off")
        plt.imshow(canvas_rgba)
        plt.tight_layout(pad=0)
        plt.savefig(frame_name, bbox_inches="tight", pad_inches=0, transparent=True)
        plt.close()
        print(f"Saved: {os.path.abspath(frame_name)}")
        # === OPTIONAL EDGE OVERLAY ===
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, threshold1=100, threshold2=200)
        edges_colored = np.zeros_like(image_rgb)
        edges_colored[edges != 0] = [255, 0, 0]  # Red edge overlay
        blended = cv2.addWeighted(canvas, 0.9, edges_colored, 0.9, 0)
        blended_rgba = np.dstack((blended, alpha))
        plt.imsave(combined_frame_name, blended_rgba)
        print(f"Saved: {os.path.abspath(combined_frame_name)}")
    else:
        # Validate that canvas is not all black/zero
        if not np.any(canvas):
            print(f"[WARNING] canvas is all black/zero before saving {frame_name}!")
        plt.figure(figsize=(width / 100, height / 100), dpi=100)
        plt.axis("off")
        plt.imshow(canvas)
        plt.tight_layout(pad=0)
        plt.savefig(frame_name, bbox_inches="tight", pad_inches=0)
        plt.close()
        print(f"Saved: {os.path.abspath(frame_name)}")
        # === OPTIONAL EDGE OVERLAY ===
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, threshold1=100, threshold2=200)
        edges_colored = np.zeros_like(image_rgb)
        edges_colored[edges != 0] = [255, 0, 0]  # Red edge overlay
        blended = cv2.addWeighted(canvas, 0.9, edges_colored, 0.9, 0)
        plt.imsave(combined_frame_name, blended)
        print(f"Saved: {os.path.abspath(combined_frame_name)}")

    # Print actual triangulation/rendering duration
    actual_duration = time.time() - checkpoint_time
    print(f"Triangulation/rendering completed in {actual_duration:.2f}s.")

    curr_time = time.time()
    frame_elapsed = curr_time - prev_time
    total_elapsed = curr_time - start_time
    frame_times.append(frame_elapsed)
    points_history.append(N)

    # Exponential fit for ETA
    if idx > 2:
        log_times = np.log(frame_times)
        fit = np.polyfit(points_history, log_times, 1)
        a = np.exp(fit[1])
        b = fit[0]
        if single_frame_mode:
            remaining = 0
        else:
            future_points = point_counts[idx:]
            future_times = [a * np.exp(b * p) for p in future_points]
            remaining = sum(future_times)
    else:
        avg_per_frame = total_elapsed / idx
        remaining = avg_per_frame * (len(point_counts) - idx)

    max_eta_seconds = 86400
    eta_seconds = int(min(remaining, max_eta_seconds))
    eta_minutes, eta_secs = divmod(eta_seconds, 60)
    finish_time = datetime.now() + timedelta(seconds=eta_seconds)
    finish_str = finish_time.strftime("%H:%M")

    total_minutes, total_secs = divmod(int(total_elapsed), 60)
    frame_minutes, frame_secs = divmod(int(frame_elapsed), 60)
    now_str = datetime.now().strftime("[%H:%M:%S]")

    print(
        f"{now_str} Saved {frame_name} | Frame: {idx}/{len(point_counts)} | Elapsed: {frame_minutes}m {frame_secs}s | Total: {total_minutes}m {total_secs}s | ETA: {eta_minutes}m {eta_secs}s (Finish by {finish_str})"
    )
    prev_time = curr_time

end_time = time.time()
done_minutes, done_secs = divmod(int(end_time - start_time), 60)
print(f"Done in {done_minutes}m {done_secs}s.")

# ===
# To control the frame generation:
# - Set single_frame_mode = True and adjust point_target for a single frame at a specific point count.
# - Set single_frame_mode = False and adjust num_frames, base_point, and factor for geometric progression.



# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:23:59+02:00
# === CUBIST FOOTER STAMP END ===
