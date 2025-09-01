# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: archive/cubist_mixedgeo_v7_20250726_211315.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:45+02:00
# === CUBIST STAMP END ===

import cv2
import numpy as np
from scipy.spatial import Delaunay, Voronoi
import os

# === CONFIG ===
INPUT_IMAGE = "statue_input_image.png"
INPUT_MASK = "edge_mask.png"
TOTAL_POINTS = 10
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

# === Step 0: Fill canvas with average color inside mask ===
average_color = tuple(np.mean(image_rgb[alpha > 0], axis=0).astype(np.uint8))
canvas = np.zeros_like(image_rgb)
for c in range(3):
    canvas[:, :, c][alpha > 0] = average_color[c]

# === Load Edge Mask ===
edge_mask_img = cv2.imread(INPUT_MASK, cv2.IMREAD_GRAYSCALE)
if edge_mask_img is None or edge_mask_img.shape != (height, width):
    raise ValueError("Edge mask not found or mismatched size.")

# === Generate Points ===
edge_coords = np.argwhere(edge_mask_img == 0)
edge_coords = np.array([pt for pt in edge_coords if alpha[pt[0], pt[1]] > 0])
edge_coords = (
    edge_coords[:, [1, 0]] if edge_coords.size else np.empty((0, 2), dtype=np.int32)
)
valid_mask = np.argwhere(alpha > 0)
remaining = TOTAL_POINTS - len(edge_coords)
idxs = np.random.choice(valid_mask.shape[0], max(0, remaining), replace=True)
random_points = valid_mask[idxs][:, [1, 0]]
corners = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
points = np.vstack((edge_coords, random_points, corners))

# === Triangulation & Voronoi ===
tri = Delaunay(points)
vor = Voronoi(points)

# === Draw Triangles ===
for simplex in tri.simplices:
    tri_pts = points[simplex].astype(np.int32)
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillConvexPoly(mask, tri_pts, 1)
    mask = np.logical_and(mask == 1, alpha > 0)
    if not np.any(mask):
        continue
    mean_color = [int(np.mean(image_rgb[:, :, c][mask])) for c in range(3)]
    canvas[mask] = mean_color

# === Optional: Mixed Geometry ===
if USE_MIXED_GEOMETRY:
    for region_idx in vor.point_region:
        region = vor.regions[region_idx]
        if -1 in region or len(region) == 0:
            continue
        polygon = np.array([vor.vertices[v] for v in region], np.int32)
        mask = np.zeros((height, width), np.uint8)
        cv2.fillPoly(mask, [polygon], 1)
        region_pixels = image_rgb[mask == 1]
        if len(region_pixels) == 0:
            continue
        mean_color = np.mean(region_pixels, axis=0)
        if mean_color.shape[0] != 3:
            continue
        color_tuple = tuple(int(x) for x in mean_color)
        cv2.fillPoly(canvas, [polygon], color_tuple)

# === Output as Transparent PNG ===
canvas_bgra = cv2.cvtColor(canvas, cv2.COLOR_RGB2BGRA)
canvas_bgra[:, :, 3] = alpha
output_path = f"frame_{frame:02d}_{len(points):05d}pts.png"
cv2.imwrite(output_path, canvas_bgra)
print(f"Saved: {os.path.abspath(output_path)}")




# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:45+02:00
# === CUBIST FOOTER STAMP END ===
