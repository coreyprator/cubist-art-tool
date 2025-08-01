#!/usr/bin/env python3
"""
Test script for CascadeFill functionality
"""
import numpy as np
import cv2
from pathlib import Path
from cubist_core_logic import run_cubist
from cubist_logger import logger

def create_test_image():
    """Create a simple test image for testing CascadeFill"""
    logger.info("create_test_image() ENTRY: Creating test image")
    # Create a 300x300 test image with some shapes
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    
    # Add some colorful shapes
    cv2.rectangle(img, (50, 50), (150, 150), (255, 0, 0), -1)  # Red square
    cv2.circle(img, (200, 100), 50, (0, 255, 0), -1)  # Green circle
    cv2.rectangle(img, (100, 180), (250, 250), (0, 0, 255), -1)  # Blue rectangle
    
    # Save test image
    test_path = Path("input/test_image.jpg")
    test_path.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(test_path), img)
    logger.info(f"Test image created: {test_path}")
    return str(test_path)

def test_cascade_modes():
    """Test all geometry modes with CascadeFill"""
    logger.info("test_cascade_modes() ENTRY: Testing cascade modes")
    test_image_path = create_test_image()
    output_dir = "output/Test_Cascade"
    
    geometry_modes = ["delaunay", "voronoi", "rectangles"]
    
    for mode in geometry_modes:
        print(f"\nTesting {mode} mode...")
        logger.info(f"Testing {mode} mode")
        
        # Test regular mode
        print(f"  - Regular {mode}")
        logger.info(f"Running regular {mode}")
        regular_output = run_cubist(
            input_path=test_image_path,
            output_dir=output_dir,
            total_points=100,
            geometry_mode=mode,
            use_cascade_fill=False,
            verbose=True
        )
        
        # Test cascade mode
        print(f"  - Cascade {mode}")
        logger.info(f"Running cascade {mode}")
        cascade_output = run_cubist(
            input_path=test_image_path,
            output_dir=output_dir,
            total_points=100,
            geometry_mode=mode,
            use_cascade_fill=True,
            verbose=True
        )
        
        print(f"  Regular output: {regular_output}")
        print(f"  Cascade output: {cascade_output}")
        logger.info(f"{mode} mode completed - Regular: {regular_output}, Cascade: {cascade_output}")

    logger.info("test_cascade_modes() EXIT: All cascade mode tests completed")

if __name__ == "__main__":
    logger.info("test_cascade_fill.py started")
    test_cascade_modes()
    logger.info("test_cascade_fill.py completed")
    print("Testing CascadeFill functionality...")
    test_cascade_modes()
    print("\nTesting complete!")
