#!/usr/bin/env python3
"""
Complete Pipeline Debug Script
This will show us exactly why SVG files aren't being created.
"""

import sys
import os
from pathlib import Path


def main():
    print("=== Pipeline Debug Analysis ===")

    # Ensure we can import the modules
    sys.path.insert(0, ".")
    from cubist_api import run_cubist
    from cubist_cli import run_pipeline

    # Run a test with verbose output
    print("1. Testing API pipeline with verbose output...")

    result = run_cubist(
        input="input/your_input_image.jpg",
        output="output/debug_test",
        geometry="delaunay",
        points=50,
        seed=1,
        export_svg=True,
        quiet=False,  # Enable verbose output
    )

    print("\\nComplete result structure:")
    for key, value in result.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"  {key}: {value}")
        elif isinstance(value, dict):
            print(f"  {key}: {{dictionary with {len(value)} keys}}")
            for subkey, subvalue in value.items():
                print(f"    {subkey}: {subvalue}")
        elif isinstance(value, list):
            print(f"  {key}: [list with {len(value)} items]")
            if value:
                print(f"    First item: {value[0]}")
        else:
            print(f"  {key}: {type(value)} - {str(value)[:100]}")

    print("\\n2. Checking output directory contents...")
    output_path = Path("output/debug_test")
    if output_path.exists():
        print(f"Output directory exists: {output_path}")
        files = list(output_path.iterdir())
        print(f"Files found: {len(files)}")
        for file in files:
            print(f"  - {file.name} ({file.stat().st_size} bytes)")
    else:
        print(f"Output directory does not exist: {output_path}")

    print("\\n3. Testing if export_svg parameter is being honored...")

    # Test with export_svg=False to see the difference
    result_no_svg = run_cubist(
        input="input/your_input_image.jpg",
        output="output/debug_no_svg",
        geometry="delaunay",
        points=50,
        seed=1,
        export_svg=False,
        quiet=False,
    )

    print("\\nResult with export_svg=False:")
    print(f"  RC: {result_no_svg.get('rc', 'MISSING')}")
    print(f"  Outputs keys: {list(result_no_svg.get('outputs', {}).keys())}")

    print("\\nResult with export_svg=True:")
    print(f"  RC: {result.get('rc', 'MISSING')}")
    print(f"  Outputs keys: {list(result.get('outputs', {}).keys())}")

    print("\\n4. Checking if CLI pipeline behaves differently...")

    cli_result = run_pipeline(
        input="input/your_input_image.jpg",
        output="output/debug_cli_test",
        geometry="delaunay",
        points=50,
        seed=1,
        export_svg=True,
        quiet=False,
    )

    print("\\nCLI pipeline result:")
    for key, value in cli_result.items():
        if key == "outputs" and isinstance(value, dict):
            print(f"  {key}: {{dictionary with {len(value)} keys}}")
            for subkey, subvalue in value.items():
                print(f"    {subkey}: {subvalue}")
        else:
            print(f"  {key}: {value}")

    print("\\n5. Testing shape generation and manual SVG export...")

    # Import and test the geometry plugin directly
    import geometry_plugins.delaunay as delaunay
    from PIL import Image
    import svg_export

    # Get canvas size
    img = Image.open("input/your_input_image.jpg")
    canvas_size = img.size

    # Generate shapes
    shapes = delaunay.generate(canvas_size=canvas_size, points=50, seed=1)
    print(f"Generated {len(shapes)} shapes from delaunay plugin")

    if shapes:
        print(f"First shape example: {shapes[0]}")

        # Try manual SVG export
        svg_content = svg_export.export_svg(
            shapes, width=canvas_size[0], height=canvas_size[1]
        )

        # Save manual SVG
        manual_svg_path = "output/manual_test.svg"
        os.makedirs("output", exist_ok=True)
        with open(manual_svg_path, "w") as f:
            f.write(svg_content)

        print(f"Manual SVG export successful: {manual_svg_path}")
        print(f"SVG file size: {Path(manual_svg_path).stat().st_size} bytes")

    print("\\n=== Debug Complete ===")
    print("This shows us exactly where the SVG export is failing in the pipeline.")


if __name__ == "__main__":
    main()
