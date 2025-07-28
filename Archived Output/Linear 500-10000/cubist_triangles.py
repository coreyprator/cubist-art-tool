import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
import time

start_time = time.time()
INPUT_IMAGE = 'your_input_image.jpg'

# === Load and resize ===
image = cv2.imread(INPUT_IMAGE)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
height, width, _ = image.shape

for POINTS in range(500, 10001, 500):
    # === Generate random points + corners ===
    points = np.vstack([
        np.random.rand(POINTS, 2) * [width, height],
        [[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]]
    ]).astype(np.int32)

    # === Triangulate ===
    tri = Delaunay(points)

    # === Create blank canvas ===
    canvas = np.zeros_like(image)

    # === Draw triangles ===
    for simplex in tri.simplices:
        pts = points[simplex].astype(np.int32)
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillConvexPoly(mask, pts, 1)

        # Compute average color within triangle
        for c in range(3):  # RGB channels
            channel = image[:, :, c]
            canvas[:, :, c][mask == 1] = int(np.mean(channel[mask == 1]))

    # === Save result ===
    OUTPUT_IMAGE = f'cubist_result_{POINTS}.jpg'
    cv2.imwrite(OUTPUT_IMAGE, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
    print(f"Saved {OUTPUT_IMAGE}")

end_time = time.time()
print(f"Done in {end_time - start_time:.2f} seconds.")
