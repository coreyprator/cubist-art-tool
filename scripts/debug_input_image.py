#!/usr/bin/env python3
"""
Debug script to trace input image processing in the Cubist Art pipeline
"""

import subprocess
import sys
import json
from pathlib import Path


def main():
    print("=== Input Image Debug Analysis ===")

    # The image path from your UI logs
    input_image = r"G:\My Drive\Code\Python\cubist_art\input\x_your_input_image.jpg"

    print(f"Testing input image: {input_image}")

    # Step 1: Verify the image file exists
    image_path = Path(input_image)
    if image_path.exists():
        size = image_path.stat().st_size
        print(f"✓ Image exists: {size:,} bytes")
    else:
        print(f"✗ Image not found at: {input_image}")
        return

    # Step 2: Test CLI directly with same parameters as UI
    print("\n=== Testing CLI Directly ===")

    test_output = "output/debug_input_test"
    cli_cmd = [
        sys.executable,
        "cubist_cli.py",
        "--input",
        input_image,
        "--output",
        test_output,
        "--geometry",
        "delaunay",
        "--points",
        "50",  # Fewer points for faster testing
        "--seed",
        "42",
        "--cascade-stages",
        "1",
        "--export-svg",
        # Removed --quiet to see verbose output
    ]

    print(f"Command: {' '.join(cli_cmd)}")
    print("Running CLI directly...")

    try:
        result = subprocess.run(cli_cmd, capture_output=True, text=True, cwd=".")

        print(f"Exit code: {result.returncode}")

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

            # Try to parse JSON output
            try:
                output_data = json.loads(result.stdout.strip())
                print("\nParsed output:")
                for key, value in output_data.items():
                    if key == "outputs":
                        print(f"  {key}:")
                        for sub_key, sub_value in value.items():
                            print(f"    {sub_key}: {sub_value}")
                    else:
                        print(f"  {key}: {value}")
            except json.JSONDecodeError:
                print("Could not parse as JSON")

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

    except Exception as e:
        print(f"Error running CLI: {e}")
        return

    # Step 3: Check if SVG was generated and examine it
    expected_svg = Path(f"{test_output}.svg")
    if expected_svg.exists():
        print(f"\n✓ SVG generated: {expected_svg}")
        svg_size = expected_svg.stat().st_size
        print(f"  Size: {svg_size:,} bytes")

        # Read first few lines to see if it looks like it processed the right image
        svg_content = expected_svg.read_text(encoding="utf-8")[:1000]
        print(f"  Preview: {svg_content[:200]}...")

        # Look for viewBox to understand image dimensions
        if "viewBox=" in svg_content:
            viewbox_start = svg_content.find("viewBox=")
            viewbox_end = svg_content.find('"', viewbox_start + 10)
            viewbox = svg_content[viewbox_start : viewbox_end + 1]
            print(f"  {viewbox}")
    else:
        print(f"✗ No SVG generated at expected path: {expected_svg}")

    # Step 4: Test with the geometry plugin directly if possible
    print("\n=== Testing Geometry Plugin Directly ===")

    try:
        # Import the delaunay plugin directly
        sys.path.insert(0, ".")
        import geometry_plugins.delaunay as delaunay_plugin

        print("✓ Delaunay plugin imported")

        # Check what functions are available
        functions = [attr for attr in dir(delaunay_plugin) if not attr.startswith("_")]
        print(f"Available functions: {functions}")

        if hasattr(delaunay_plugin, "generate"):
            print("Testing delaunay.generate() directly...")

            # Get image dimensions for canvas_size
            try:
                from PIL import Image

                with Image.open(input_image) as img:
                    canvas_size = img.size
                    print(f"Image dimensions: {canvas_size}")

                # Test the generate function
                shapes = delaunay_plugin.generate(
                    canvas_size=canvas_size, points=50, seed=42
                )
                print(f"✓ Generated {len(shapes)} shapes directly")

                if shapes:
                    first_shape = shapes[0]
                    print(f"First shape example: {first_shape}")

                    # Check if the shape coordinates make sense for the image
                    if "points" in first_shape:
                        points = first_shape["points"]
                        if points:
                            x_coords = [p[0] for p in points]
                            y_coords = [p[1] for p in points]
                            print(
                                f"Point range: X({min(x_coords):.1f}-{max(x_coords):.1f}), Y({min(y_coords):.1f}-{max(y_coords):.1f})"
                            )
                            print(f"Image size: {canvas_size}")

                            # Check if points are within image bounds
                            within_bounds = all(
                                0 <= x <= canvas_size[0] and 0 <= y <= canvas_size[1]
                                for x, y in points
                            )
                            print(f"Points within image bounds: {within_bounds}")

            except Exception as e:
                print(f"Error testing plugin directly: {e}")
        else:
            print("No generate() function found")

    except ImportError as e:
        print(f"Could not import delaunay plugin: {e}")

    print("\n=== Analysis Complete ===")
    print("\nIf the CLI test worked but generated simple shapes,")
    print("the issue might be in how the geometry plugin processes your image.")
    print("Look at the coordinate ranges - they should reflect your image dimensions.")


if __name__ == "__main__":
    main()
