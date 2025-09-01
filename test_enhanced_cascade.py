#!/usr/bin/env python3
# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: test_enhanced_cascade.py
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:28+02:00
# === CUBIST STAMP END ===

"""
Test script for enhanced CascadeFill functionality.
This script tests the spatial optimization and adjacency-based placement.
"""

import sys
import os
from pathlib import Path
import numpy as np
import cv2

try:
    from cubist_core_logic import run_cubist
except ImportError:
    print("ERROR: Could not import cubist_core_logic.py")
    sys.exit(1)


def create_test_image():
    """Create a simple test image for testing."""
    # Create a 400x400 RGB image with a gradient
    img = np.zeros((400, 400, 3), dtype=np.uint8)

    # Create gradient background
    for y in range(400):
        for x in range(400):
            img[y, x] = [
                int(255 * x / 400),  # Red gradient
                int(255 * y / 400),  # Green gradient
                int(128 + 127 * np.sin(x * 0.02) * np.cos(y * 0.02)),  # Blue pattern
            ]

    return img


def test_enhanced_cascade_fill():
    """Test the enhanced cascade fill functionality."""
    print("🧪 Testing Enhanced CascadeFill Functionality")
    print("=" * 50)

    # Create test image
    test_image = create_test_image()

    # Save test image
    test_input_path = "test_input_gradient.png"
    cv2.imwrite(test_input_path, cv2.cvtColor(test_image, cv2.COLOR_RGB2BGR))
    print(f"📁 Created test image: {test_input_path}")

    # Create output directory
    output_dir = "test_output"
    Path(output_dir).mkdir(exist_ok=True)

    # Test parameters
    test_cases = [
        {
            "geometry": "delaunay",
            "points": 100,
            "desc": "Delaunay triangulation with spatial optimization",
        },
        {
            "geometry": "voronoi",
            "points": 80,
            "desc": "Voronoi cells with adjacency-based placement",
        },
        {
            "geometry": "rectangles",
            "points": 120,
            "desc": "Rectangles with rotational variety",
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔄 Test {i}/3: {test_case['desc']}")
        print(f"   Geometry: {test_case['geometry']}, Points: {test_case['points']}")

        try:
            # Test with enhanced cascade fill
            output_path = run_cubist(
                input_path=test_input_path,
                output_dir=output_dir,
                mask_path=None,
                total_points=test_case["points"],
                clip_to_alpha=True,
                verbose=True,
                geometry_mode=test_case["geometry"],
                use_cascade_fill=True,
                save_step_frames=False,
            )

            print(f"✅ SUCCESS: {test_case['geometry']} cascade fill completed")
            print(f"📁 Output: {output_path}")
            results.append((test_case["geometry"], True, output_path))

        except Exception as e:
            print(f"❌ ERROR: {test_case['geometry']} failed - {str(e)}")
            results.append((test_case["geometry"], False, None))

    # Test regular tessellation for comparison
    print("\n🔄 Comparison Test: Regular tessellation")
    try:
        comparison_path = run_cubist(
            input_path=test_input_path,
            output_dir=output_dir,
            mask_path=None,
            total_points=100,
            clip_to_alpha=True,
            verbose=True,
            geometry_mode="delaunay",
            use_cascade_fill=False,
            save_step_frames=False,
        )
        print("✅ SUCCESS: Regular tessellation completed")
        print(f"📁 Comparison output: {comparison_path}")
        results.append(("regular_delaunay", True, comparison_path))
    except Exception as e:
        print(f"❌ ERROR: Regular tessellation failed - {str(e)}")
        results.append(("regular_delaunay", False, None))

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 TEST SUMMARY")
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
                print(f"  • {mode:>15} | {filename}")

    if failed:
        print("\n❌ Failed Tests:")
        for mode, success, path in failed:
            print(f"  • {mode:>15}")

    print("\n💡 Compare the enhanced cascade fill outputs with regular tessellation!")
    print("   Look for:")
    print("   - Better space utilization (fewer gaps)")
    print("   - Adjacency-based placement (shapes near each other)")
    print("   - Variety in shape sizes and orientations")

    # Cleanup
    if os.path.exists(test_input_path):
        os.remove(test_input_path)
        print("\n🧹 Cleaned up test input file")


if __name__ == "__main__":
    test_enhanced_cascade_fill()


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:28+02:00
# === CUBIST FOOTER STAMP END ===
