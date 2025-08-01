#!/usr/bin/env python3
"""
Test script for CascadeFill animation functionality
"""
import numpy as np
import cv2
from pathlib import Path
from cubist_core_logic import run_cubist

def create_simple_test_image():
    """Create a very simple test image for animation testing"""
    # Create a 200x200 test image
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    
    # Add a simple gradient
    for y in range(200):
        for x in range(200):
            img[y, x] = [x // 2, y // 2, (x + y) // 4]
    
    # Save test image
    test_path = Path("input/animation_test.jpg")
    test_path.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(test_path), img)
    return str(test_path)

def test_animation_frames():
    """Test CascadeFill with animation frames"""
    test_image_path = create_simple_test_image()
    output_dir = "output/Animation_Test"
    
    print("Testing CascadeFill with animation frames...")
    
    # Test cascade mode with animation
    cascade_output = run_cubist(
        input_path=test_image_path,
        output_dir=output_dir,
        total_points=50,  # Smaller number for faster testing
        geometry_mode="rectangles",  # Rectangles are fastest for testing
        use_cascade_fill=True,
        save_step_frames=True,  # Enable animation frames
        verbose=True
    )
    
    print(f"Final output: {cascade_output}")
    print("Check the output directory for step frames!")

if __name__ == "__main__":
    test_animation_frames()
