#!/usr/bin/env python3
# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: test_rectangle_variations.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:23:58+02:00
# === CUBIST STAMP END ===

"""
Test script for enhanced rectangle generation in CascadeFill mode.
This script specifically tests the independent width/height functionality.
"""

import sys
import os
from pathlib import Path
import numpy as np
import cv2

try:
    from cubist_core_logic import run_cubist
    from cubist_logger import logger
except ImportError:
    print("ERROR: Could not import required modules")
    sys.exit(1)


def create_test_image():
    """Create a simple test image optimized for rectangle testing."""
    logger.info("create_test_image() ENTRY: Creating rectangle test image")
    # Create a 500x500 RGB image with distinct regions
    img = np.zeros((500, 500, 3), dtype=np.uint8)

    # Create colorful regions for better rectangle visibility
    # Top-left: Red gradient
    img[0:250, 0:250] = [255, 100, 100]
    # Top-right: Green gradient
    img[0:250, 250:500] = [100, 255, 100]
    # Bottom-left: Blue gradient
    img[250:500, 0:250] = [100, 100, 255]
    # Bottom-right: Yellow gradient
    img[250:500, 250:500] = [255, 255, 100]

    # Add some texture
    for y in range(500):
        for x in range(500):
            noise = int(30 * np.sin(x * 0.05) * np.cos(y * 0.05))
            img[y, x] = np.clip(img[y, x].astype(int) + noise, 0, 255).astype(np.uint8)

    return img


def test_rectangle_variations():
    """Test the enhanced rectangle functionality with independent width/height."""
    logger.info(
        "test_rectangle_variations() ENTRY: Testing enhanced rectangle generation"
    )
    print("🟦 Testing Enhanced Rectangle Generation")
    print("=" * 50)

    # Create test image
    test_image = create_test_image()

    # Save test image
    test_input_path = "test_input_rectangles.png"
    cv2.imwrite(test_input_path, cv2.cvtColor(test_image, cv2.COLOR_RGB2BGR))
    print(f"📁 Created test image: {test_input_path}")
    logger.info(f"Test image saved: {test_input_path}")

    # Create output directory
    output_dir = "test_output"
    Path(output_dir).mkdir(exist_ok=True)
    logger.info(f"Output directory created: {output_dir}")

    # Test different point counts for different rectangle densities
    test_cases = [
        {"points": 50, "desc": "Sparse rectangles (large, varied shapes)"},
        {"points": 150, "desc": "Medium density rectangles"},
        {"points": 300, "desc": "Dense rectangles (small, varied shapes)"},
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔄 Test {i}/3: {test_case['desc']}")
        print(f"   Points: {test_case['points']}")
        logger.info(
            f"Starting test case {i}: {test_case['desc']} with {test_case['points']} points"
        )

        try:
            # Test enhanced rectangle cascade fill
            output_path = run_cubist(
                input_path=test_input_path,
                output_dir=output_dir,
                mask_path=None,
                total_points=test_case["points"],
                clip_to_alpha=True,
                verbose=True,
                geometry_mode="rectangles",
                use_cascade_fill=True,
                save_step_frames=False,
            )

            print("✅ SUCCESS: Rectangle cascade fill completed")
            print(f"📁 Output: {output_path}")
            results.append((f"rectangles_{test_case['points']}", True, output_path))

        except Exception as e:
            print(f"❌ ERROR: Rectangle test failed - {str(e)}")
            results.append((f"rectangles_{test_case['points']}", False, None))

    # Test regular rectangles for comparison
    print("\n🔄 Comparison Test: Regular rectangle tessellation")
    try:
        comparison_path = run_cubist(
            input_path=test_input_path,
            output_dir=output_dir,
            mask_path=None,
            total_points=150,
            clip_to_alpha=True,
            verbose=True,
            geometry_mode="rectangles",
            use_cascade_fill=False,
            save_step_frames=False,
        )
        print("✅ SUCCESS: Regular rectangle tessellation completed")
        print(f"📁 Comparison output: {comparison_path}")
        results.append(("rectangles_regular", True, comparison_path))
    except Exception as e:
        print(f"❌ ERROR: Regular rectangles failed - {str(e)}")
        results.append(("rectangles_regular", False, None))

    # Test with step frames to see the progressive filling
    print("\n🔄 Animation Test: Rectangle cascade with step frames")
    try:
        animation_path = run_cubist(
            input_path=test_input_path,
            output_dir=output_dir,
            mask_path=None,
            total_points=100,
            clip_to_alpha=True,
            verbose=True,
            geometry_mode="rectangles",
            use_cascade_fill=True,
            save_step_frames=True,
        )
        print("✅ SUCCESS: Rectangle animation frames generated")
        print(f"📁 Final frame: {animation_path}")
        print(f"📁 Step frames: Check {output_dir}/cascade_step_*_rectangles.png")
        results.append(("rectangles_animation", True, animation_path))
    except Exception as e:
        print(f"❌ ERROR: Rectangle animation failed - {str(e)}")
        results.append(("rectangles_animation", False, None))

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 RECTANGLE TEST SUMMARY")
    print(f"{'=' * 60}")

    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")

    if successful:
        print("\n📁 Generated Files:")
        for mode, success, path in successful:
            if path:
                filename = Path(path).name
                print(f"  • {mode:>20} | {filename}")

    if failed:
        print("\n❌ Failed Tests:")
        for mode, success, path in failed:
            print(f"  • {mode:>20}")

    print("\n💡 Enhanced Rectangle Features to Look For:")
    print("   ✨ Independent width and height (aspect ratios 0.5-2.0)")
    print("   ✨ Varied rectangle shapes (not just squares)")
    print("   ✨ Better space filling with different sized rectangles")
    print("   ✨ Rotational variety for organic appearance")
    print("   ✨ Centered placement with proper boundary clamping")
    print("\n🎨 Compare with regular tessellation to see the difference!")

    # Cleanup
    if os.path.exists(test_input_path):
        os.remove(test_input_path)
        print("\n🧹 Cleaned up test input file")


if __name__ == "__main__":
    logger.info("test_rectangle_variations.py started")
    test_rectangle_variations()
    logger.info("test_rectangle_variations.py completed")


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:23:58+02:00
# === CUBIST FOOTER STAMP END ===
