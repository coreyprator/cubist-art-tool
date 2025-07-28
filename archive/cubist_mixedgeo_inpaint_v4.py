
import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay, Voronoi
import time
import os
import json
from datetime import datetime

# Program metadata
program_start = datetime.now()
cwd = os.getcwd()
print(f"[START {program_start.strftime('%H:%M:%S')}] Program started.")
print(f"Current working directory: {cwd}")

# === Configuration ===
INPUT_IMAGE = 'statue_input_image.png'
EDGE_MASK_PATH = 'edge_mask.png'
TOTAL_POINTS = 1000
USE_MIXED_GEOMETRY = True
CLIP_TRIANGLES_TO_ALPHA = True
FRAME = 1
POINT_COUNT = TOTAL_POINTS

# === Image and Mask Load ===
image_bgra = cv2.imread(INPUT_IMAGE, cv2.IMREAD_UNCHANGED)
if image_bgra is None:
    raise FileNotFoundError(f"Could not load image: {INPUT_IMAGE}")
if image_bgra.shape[2] == 4:
    image_rgb = cv2.cvtColor(image_bgra[:, :, :3], cv2.COLOR_BGR2RGB)
    alpha = image_bgra[:, :, 3]
else:
    image_rgb = cv2.cvtColor(image_bgra, cv2.COLOR_BGR2RGB)
    alpha = np.ones(image_rgb.shape[:2], dtype=np.uint8) * 255

height, width = image_rgb.shape[:2]

edge_mask = cv2.imread(EDGE_MASK_PATH, cv2.IMREAD_GRAYSCALE)
if edge_mask is None or edge_mask.shape != (height, width):
    raise FileNotFoundError(f"Edge mask '{EDGE_MASK_PATH}' not found or mismatched.")

# === Generate Points ===
edge_coords = np.argwhere(edge_mask == 0)
edge_coords = np.array([pt for pt in edge_coords if alpha[pt[0], pt[1]] > 0])
edge_coords = edge_coords[:, [1, 0]] if edge_coords.size else np.empty((0, 2), dtype=np.int32)
valid_mask = np.argwhere(alpha > 0)
num_random = TOTAL_POINTS - len(edge_coords)
idxs = np.random.choice(valid_mask.shape[0], num_random, replace=True)
random_points = valid_mask[idxs][:, [1, 0]]
corners = np.array([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]])
points = np.vstack((edge_coords, random_points, corners))

# === Triangulation and Voronoi ===
tri = Delaunay(points)
vor = Voronoi(points)
canvas = np.zeros_like(image_rgb)

# === Triangles ===
for simplex in tri.simplices:
    tri_pts = points[simplex].astype(np.int32)
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillConvexPoly(mask, tri_pts, 1)
    mask = np.logical_and(mask == 1, alpha > 0)
    if not np.any(mask): continue
    mean_color = [int(np.mean(image_rgb[:, :, c][mask])) for c in range(3)]
    canvas[mask] = mean_color

# === Mixed Geometry ===
if USE_MIXED_GEOMETRY:
    for i, region_idx in enumerate(vor.point_region):
        region = vor.regions[region_idx]
        if -1 in region or len(region) == 0: continue
        polygon = np.array([vor.vertices[v] for v in region], np.int32)
        mask = np.zeros((height, width), np.uint8)
        cv2.fillPoly(mask, [polygon], 1)
        region_pixels = image_rgb[mask == 1]
        if len(region_pixels) == 0: continue
        mean_color = np.mean(region_pixels, axis=0)
        if mean_color.shape[0] != 3: continue
        color_std = np.std(region_pixels)
        color_tuple = tuple(int(x) for x in mean_color)
        if color_std < 20:
            (x, y), radius = cv2.minEnclosingCircle(polygon)
            if radius < 5:
                rect = cv2.boundingRect(polygon)
                cv2.rectangle(canvas, (rect[0], rect[1]), (rect[0]+rect[2], rect[1]+rect[3]), color_tuple, -1)
            else:
                cv2.circle(canvas, (int(x), int(y)), int(radius), color_tuple, -1)
        else:
            cv2.fillPoly(canvas, [polygon], color_tuple)

# === Inpainting ===
void_mask = ((np.sum(canvas, axis=2) <= 3) & (alpha > 0)).astype(np.uint8)
void_mask_path = f'void_mask_{FRAME:02d}_{POINT_COUNT:05d}pts.png'
cv2.imwrite(void_mask_path, void_mask * 255)
print(f"Saved: {os.path.abspath(void_mask_path)} (void mask)")

pre_canvas_path = f'debug_pre_inpaint_{FRAME:02d}_{POINT_COUNT:05d}.png'
cv2.imwrite(pre_canvas_path, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
print(f"Saved: {os.path.abspath(pre_canvas_path)} (pre-inpaint canvas)")

kernel = np.ones((3, 3), np.uint8)
void_mask_dilated = cv2.dilate(void_mask, kernel, iterations=1)

if np.any(void_mask_dilated):
    canvas_bgr = cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR)
    inpainted = cv2.inpaint(canvas_bgr, void_mask_dilated, 3, cv2.INPAINT_TELEA)
    canvas = cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)

    post_canvas_path = f'debug_post_inpaint_{FRAME:02d}_{POINT_COUNT:05d}.png'
    cv2.imwrite(post_canvas_path, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
    print(f"Saved: {os.path.abspath(post_canvas_path)} (post-inpaint canvas)")

    remaining_void = ((np.sum(canvas, axis=2) <= 3) & (alpha > 0))
    if np.any(remaining_void):
        print(f"[WARNING] Remaining near-black voids after inpainting.")
        fallback_mask_path = f'void_mask_fallback_{FRAME:02d}_{POINT_COUNT:05d}pts.png'
        cv2.imwrite(fallback_mask_path, remaining_void.astype(np.uint8) * 255)
        print(f"Saved: {os.path.abspath(fallback_mask_path)} (fallback void mask)")
        neutral_color = tuple(int(x) for x in np.mean(image_rgb[alpha > 0], axis=0))
        for c in range(3):
            canvas[:, :, c][remaining_void] = neutral_color[c]

# === Final Save ===
frame_path = f'frame_{FRAME:02d}_{POINT_COUNT:05d}pts.png'
cv2.imwrite(frame_path, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
print(f"Saved: {os.path.abspath(frame_path)} (final image)")
