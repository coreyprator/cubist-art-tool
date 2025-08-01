
# test_geometry_modes.py


import sys
import os
# Add parent directory to sys.path so imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cubist_core_logic import run_cubist
from cubist_logger import log_message
import cv2
import datetime

INPUT_IMAGE = "G:/My Drive/Code/Python/cubist_art/input/your_input_image.jpg"  # Update this with your actual image path
OUTPUT_DIR = "output/tests"
LOG_FILE = os.path.join(OUTPUT_DIR, "run_log.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)


geometry_modes = ["delaunay", "voronoi", "rectangles", "invalid_mode"]
MASK_PATH = "G:/My Drive/Code/Python/cubist_art/input/edge_mask.png"


def log_exception(mode, exc):
    log_message(f"EXCEPTION: {mode} failed with error: [{type(exc).__name__}: {exc}]", level="error")


def overlay_mode_on_image(image_path, mode):
    try:
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            return
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        color = (0, 0, 255, 255) if img.shape[2] == 4 else (0, 0, 255)
        thickness = 2
        text = f"{mode.upper()}"
        (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
        x, y = 10, th + 10
        if img.shape[2] == 4:
            overlay = img.copy()
            cv2.putText(overlay, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)
            alpha = 0.7
            cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        else:
            cv2.putText(img, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)
        cv2.imwrite(image_path, img)
    except Exception as e:
        log_exception(mode, e)



for mask_setting, mask_label in [(None, "no mask"), (MASK_PATH, "with mask")]:
    for mode in geometry_modes:
        log_message(f"Starting geometry mode: {mode} ({mask_label})")
        print(f"\n--- Testing {mode} ({mask_label}) ---")
        try:
            output_path = run_cubist(
                input_path=INPUT_IMAGE,
                output_dir=OUTPUT_DIR,
                mask_path=mask_setting,
                total_points=500,
                clip_to_alpha=False,
                verbose=True,
                geometry_mode=mode
            )
            if mode != "invalid_mode":
                overlay_mode_on_image(output_path, mode)
            log_message(f"SUCCESS: {mode} ({mask_label}) completed successfully")
            print(f"[{mode}] SUCCESS: Output saved to {output_path}")
        except Exception as e:
            log_exception(mode, e)
            print(f"[{mode}] FAILURE: {type(e).__name__}: {e}")
        finally:
            log_message(f"Finished geometry mode: {mode} ({mask_label})")

log_message("All geometry tests complete.")
