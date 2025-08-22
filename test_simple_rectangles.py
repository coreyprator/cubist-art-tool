#!/usr/bin/env python3
"""
Simple test to verify the rectangle generation logic works correctly.
"""

import numpy as np
from cubist_core_logic import generate_shape_mask


def test_rectangle_generation():
    """Test the rectangle generation function directly."""
    print("Testing rectangle generation logic...")

    # Test parameters
    image_shape = (200, 200)  # Small test image
    center_x, center_y = 100, 100
    size = 40

    # Create simple available mask
    available_mask = np.ones(image_shape, dtype=bool)
    occupied_mask = np.zeros(image_shape, dtype=bool)

    print("Generating test rectangles...")

    # Test multiple rectangles
    for i in range(5):
        print(f"  Rectangle {i + 1}/5")

        mask = generate_shape_mask(
            center_x=center_x + i * 10,
            center_y=center_y + i * 10,
            size=size - i * 5,
            mode="rectangles",
            image_shape=image_shape,
            available_mask=available_mask,
            occupied_mask=occupied_mask,
        )

        if mask is not None:
            area = np.sum(mask)
            print(f"    ✅ Generated rectangle with area: {area} pixels")
            # Update occupied mask
            occupied_mask |= mask
        else:
            print("    ❌ Failed to generate rectangle")

    print("Rectangle generation test completed!")


if __name__ == "__main__":
    test_rectangle_generation()
