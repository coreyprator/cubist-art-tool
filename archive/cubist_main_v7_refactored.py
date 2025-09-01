# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: archive/cubist_main_v7_refactored.py
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:30+02:00
# === CUBIST STAMP END ===

import os
import cv2
import numpy as np
from scipy.spatial import Delaunay


def run_cubist(input_path, output_dir, total_points=1000, clip_to_alpha=True):
    image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(f"Input image not found: {input_path}")

    if image.shape[2] == 4:
        rgb = image[:, :, :3]
        alpha = image[:, :, 3]
    else:
        rgb = image
        alpha = np.ones(rgb.shape[:2], dtype=np.uint8) * 255

    height, width = rgb.shape[:2]
    canvas = np.zeros_like(rgb)

    valid_mask = np.argwhere(alpha > 0)
    if valid_mask.shape[0] < total_points:
        chosen = valid_mask[
            np.random.choice(valid_mask.shape[0], total_points, replace=True)
        ]
    else:
        chosen = valid_mask[
            np.random.choice(valid_mask.shape[0], total_points, replace=False)
        ]

    points = chosen[:, [1, 0]]
    tri = Delaunay(points)

    for simplex in tri.simplices:
        pts = points[simplex].astype(np.int32)
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillConvexPoly(mask, pts, 1)
        if clip_to_alpha:
            mask = np.logical_and(mask == 1, alpha > 0)
        else:
            mask = mask == 1
        if not np.any(mask):
            continue
        color = [int(np.mean(rgb[:, :, c][mask])) for c in range(3)]
        for c in range(3):
            canvas[:, :, c][mask] = color[c]

    suffix = f"{total_points:05d}"
    out_path = os.path.join(output_dir, f"frame_01_{suffix}pts.png")
    cv2.imwrite(out_path, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
    print(f"Saved: {out_path}")


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:30+02:00
# === CUBIST FOOTER STAMP END ===
