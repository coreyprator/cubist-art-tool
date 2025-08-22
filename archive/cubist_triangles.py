import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
import time

start_time = time.time()
INPUT_IMAGE = "your_input_image.jpg"

# === Load and resize ===
image = cv2.imread(INPUT_IMAGE)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
height, width, _ = image.shape

# Generate a fixed list of 10,000 random points
TOTAL_POINTS = 10000
fixed_points = np.random.rand(TOTAL_POINTS, 2) * [width, height]
corners = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])

num_frames = 20
factor = 1.53

prev_time = start_time
for frame in range(1, num_frames + 1):
    N = min(int(2 * (factor ** (frame - 1))), TOTAL_POINTS)
    points = np.vstack([fixed_points[:N], corners])

    tri = Delaunay(points)
    canvas = np.zeros_like(image)

    for simplex in tri.simplices:
        pts = points[simplex].astype(np.int32)
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillConvexPoly(mask, pts, 1)
        mean_color = [int(np.mean(image[:, :, c][mask == 1])) for c in range(3)]
        canvas[mask == 1] = mean_color

    plt.figure(figsize=(width / 100, height / 100), dpi=100)
    plt.axis("off")
    plt.imshow(canvas)
    plt.tight_layout(pad=0)
    frame_name = f"frame_{frame:02d}.png"
    plt.savefig(frame_name, bbox_inches="tight", pad_inches=0)
    plt.close()

    curr_time = time.time()
    print(
        f"Saved {frame_name} | Frame elapsed: {curr_time - prev_time:.2f}s | Total elapsed: {curr_time - start_time:.2f}s"
    )
    prev_time = curr_time

end_time = time.time()
print(f"Done in {end_time - start_time:.2f} seconds.")
