# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: archive/cubist_geometry_v5.py
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:30+02:00
# === CUBIST STAMP END ===

import cv2
import numpy as np
from scipy.spatial import Delaunay, Voronoi
import os
from datetime import datetime

# === Start Logging ===
program_start = datetime.now()
cwd = os.getcwd()
print(f"[START {program_start.strftime('%H:%M:%S')}] Program started.")
print(f"Current working directory: {cwd}")

# === Config ===
INPUT_IMAGE = "statue_input_image.png"
INPUT_MASK = "edge_mask.png"
TOTAL_POINTS = 1000
EDGE_FRACTION = 0.2
USE_MIXED_GEOMETRY = True
frame = 1

# === Load Image and Alpha ===
image_bgra = cv2.imread(INPUT_IMAGE, cv2.IMREAD_UNCHANGED)
if image_bgra.shape[2] == 4:
    image_rgb = cv2.cvtColor(image_bgra[:, :, :3], cv2.COLOR_BGR2RGB)
    alpha = image_bgra[:, :, 3]
else:
    image_rgb = cv2.cvtColor(image_bgra, cv2.COLOR_BGR2RGB)
    alpha = np.ones(image_rgb.shape[:2], dtype=np.uint8) * 255

height, width = image_rgb.shape[:2]

# === Pre-fill canvas with average color inside mask ===
avg_color = tuple(int(c) for c in np.mean(image_rgb[alpha > 0], axis=0))
canvas = np.zeros_like(image_rgb)
for c in range(3):
    canvas[:, :, c][alpha > 0] = avg_color[c]

# === Load Edge Mask ===
edge_mask_img = cv2.imread(INPUT_MASK, cv2.IMREAD_GRAYSCALE)
if edge_mask_img is None or edge_mask_img.shape != (height, width):
    raise ValueError("Edge mask not found or mismatched size.")

# === Point Sampling ===
edge_coords = np.argwhere(edge_mask_img == 0)
edge_coords = np.array([pt for pt in edge_coords if alpha[pt[0], pt[1]] > 0])
edge_coords = (
    edge_coords[:, [1, 0]] if edge_coords.size else np.empty((0, 2), dtype=np.int32)
)
valid_mask = np.argwhere(alpha > 0)
remaining = TOTAL_POINTS - len(edge_coords)
idxs = np.random.choice(valid_mask.shape[0], remaining, replace=True)
random_points = valid_mask[idxs][:, [1, 0]]
corners = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
points = np.vstack((edge_coords, random_points, corners))

# === Triangles ===
tri = Delaunay(points)
for simplex in tri.simplices:
    tri_pts = points[simplex].astype(np.int32)
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillConvexPoly(mask, tri_pts, 1)
    mask = np.logical_and(mask == 1, alpha > 0)
    if not np.any(mask):
        continue
    mean_color = [int(np.mean(image_rgb[:, :, c][mask])) for c in range(3)]
    canvas[mask] = mean_color

# === Mixed Geometry (Voronoi) ===
if USE_MIXED_GEOMETRY:
    vor = Voronoi(points)
    for region_idx in vor.point_region:
        region = vor.regions[region_idx]
        if -1 in region or len(region) == 0:
            continue
        polygon = np.array([vor.vertices[v] for v in region], np.int32)
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, [polygon], 1)
        region_pixels = image_rgb[mask == 1]
        if len(region_pixels) == 0:
            continue
        mean_color = np.mean(region_pixels, axis=0)
        color_std = np.std(region_pixels)
        color_tuple = tuple(int(x) for x in mean_color)
        if color_std < 20:
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
        else:
            cv2.fillPoly(canvas, [polygon], color_tuple)

# === Save Final Output ===
frame_name = f"frame_{frame:02d}_{TOTAL_POINTS:05d}pts.png"
cv2.imwrite(frame_name, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
print(f"Saved final output: {os.path.abspath(frame_name)}")


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:30+02:00
# === CUBIST FOOTER STAMP END ===
