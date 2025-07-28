
import os
import cv2
import numpy as np

def run_cubist_pipeline(input_path, output_dir, total_points=1000, clip_to_alpha=True, mask_path=None):
    try:
        image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise FileNotFoundError(f"Input image not found: {input_path}")

        if mask_path and os.path.exists(mask_path):
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            if mask is None or mask.shape[:2] != image.shape[:2]:
                raise ValueError("Mask size does not match image or is unreadable")
        else:
            mask = np.ones(image.shape[:2], dtype=np.uint8) * 255

        canvas = np.full(image.shape[:2] + (3,), fill_value=int(np.mean(image[mask > 0])), dtype=np.uint8)

        h, w = image.shape[:2]
        pts = np.random.randint(0, [w, h], size=(total_points, 2))
        for pt in pts:
            x, y = pt
            if mask[y, x] > 0:
                canvas[y, x] = image[y, x][:3] if image.shape[2] == 4 else image[y, x]

        filename = f"frame_01_{total_points:05d}pts.png"
        out_path = os.path.join(output_dir, filename)
        cv2.imwrite(out_path, canvas)
        return out_path
    except Exception as e:
        print(f"[ERROR] {e}")
        return None
