# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: archive/cubist_mixedgeo_v6_20250726_210105.py
# Version: v2.3.4
# Build: 2025-09-01T08:25:00
# Commit: n/a
# Stamped: 2025-09-01T08:36:05
# === CUBIST STAMP END ===
import cv2
import numpy as np
from scipy.spatial import Delaunay, Voronoi
import os
from datetime import datetime

# === Init ===
program_start = datetime.now()
cwd = os.getcwd()
print(f"[START {program_start.strftime('%H:%M:%S')}] Program started.")
print(f"Current working directory: {cwd}")

# === Config ===
INPUT_IMAGE = "statue_input_image.png"
INPUT_MASK = "edge_mask.png"
TOTAL_POINTS = 1000
USE_MIXED_GEOMETRY = True
frame = 1

# === Load Image ===
image_bgra = cv2.imread(INPUT_IMAGE, cv2.IMREAD_UNCHANGED)
if image_bgra.shape[2] == 4:
    image_rgb = cv2.cvtColor(image_bgra[:, :, :3], cv2.COLOR_BGR2RGB)
    alpha = image_bgra[:, :, 3]
else:
    image_rgb = cv2.cvtColor(image_bgra, cv2.COLOR_BGR2RGB)
    alpha = np.ones(image_rgb.shape[:2], dtype=np.uint8) * 255

height, width = image_rgb.shape[:2]

# === Pre-fill canvas with average color inside alpha > 0 ===
canvas = np.zeros_like(image_rgb)
neutral_color = tuple(int(x) for x in np.mean(image_rgb[alpha > 0], axis=0))
for c in range(3):
    canvas[:, :, c][alpha > 0] = neutral_color[c]

# === Load Edge Mask ===
edge_mask_img = cv2.imread(INPUT_MASK, cv2.IMREAD_GRAYSCALE)
if edge_mask_img is None or edge_mask_img.shape != (height, width):
    raise ValueError("Edge mask not found or mismatched size.")

# === Point Generation ===
edge_coords = np.argwhere(edge_mask_img == 0)
edge_coords = np.array([pt for pt in edge_coords if alpha[pt[0], pt[1]] > 0])
edge_coords = (
    edge_coords[:, [1, 0]] if edge_coords.size else np.empty((0, 2), dtype=np.int32)
)
valid_mask = np.argwhere(alpha > 0)
idxs = np.random.choice(
    valid_mask.shape[0], TOTAL_POINTS - len(edge_coords), replace=True
)
random_points = valid_mask[idxs][:, [1, 0]]
corners = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
points = np.vstack((edge_coords, random_points, corners))

# === Geometry ===
tri = Delaunay(points)
vor = Voronoi(points)

# === Triangle Rendering with Mask Clipping ===
for simplex in tri.simplices:
    tri_pts = points[simplex].astype(np.int32)
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillConvexPoly(mask, tri_pts, 1)
    valid_area = np.logical_and(mask == 1, alpha > 0)
    if not np.any(valid_area):
        continue
    mean_color = [int(np.mean(image_rgb[:, :, c][valid_area])) for c in range(3)]
    for c in range(3):
        canvas[:, :, c][valid_area] = mean_color[c]

# === Mixed Geometry Rendering ===
if USE_MIXED_GEOMETRY:
    for region_idx in vor.point_region:
        region = vor.regions[region_idx]
        if -1 in region or len(region) == 0:
            continue
        polygon = np.array([vor.vertices[v] for v in region], np.int32)
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, [polygon], 1)
        valid_area = np.logical_and(mask == 1, alpha > 0)
        region_pixels = image_rgb[valid_area]
        if len(region_pixels) == 0:
            continue
        mean_color = np.mean(region_pixels, axis=0).astype(np.uint8)
        for c in range(3):
            canvas[:, :, c][valid_area] = mean_color[c]

# === Save Output ===
output_name = f"frame_{frame:02d}_{TOTAL_POINTS:05d}pts.png"
cv2.imwrite(output_name, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
print(f"Saved: {os.path.abspath(output_name)}")
# === CUBIST FOOTER STAMP BEGIN ===
# End of file — v2.3.4 — stamped 2025-09-01T08:36:05
# === CUBIST FOOTER STAMP END ===
