#!/usr/bin/env python3
"""
Cubism Art Output Diagnostic Script
Run this to diagnose why SVG files aren't being generated.
"""

import sys
import os
from pathlib import Path
import traceback


def main():
    print("=== Cubism Art Output Diagnostic ===")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print()

    # Step 1: Check if we can import the main modules
    print("1. Testing imports...")
    try:
        sys.path.insert(0, ".")
        from cubist_api import run_cubist

        print("   ✓ cubist_api.run_cubist imported successfully")

        from cubist_cli import run_pipeline

        print("   ✓ cubist_cli.run_pipeline imported successfully")

        import svg_export

        print("   ✓ svg_export imported successfully")

    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        traceback.print_exc()
        return False

    # Step 2: Check if input files exist
    print("\n2. Checking input files...")
    input_candidates = [
        "input/your_input_image.jpg",
        "input/test_image.jpg",
        "input/bg_your_input_image.jpg",
    ]

    working_input = None
    for candidate in input_candidates:
        if Path(candidate).exists():
            print(f"   ✓ Found input: {candidate}")
            working_input = candidate
            break
        else:
            print(f"   - Missing: {candidate}")

    if not working_input:
        print("   ⚠ No input images found - creating a test image")
        # Create a simple test image using PIL
        try:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (400, 300), color="lightblue")
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 350, 250], fill="white", outline="black", width=2)
            draw.text((200, 150), "TEST", fill="black", anchor="mm")

            os.makedirs("input", exist_ok=True)
            test_path = "input/test_image.jpg"
            img.save(test_path)
            working_input = test_path
            print(f"   ✓ Created test image: {test_path}")
        except Exception as e:
            print(f"   ✗ Failed to create test image: {e}")
            return False

    # Step 3: Test the canvas size issue mentioned in handoff
    print("\n3. Testing canvas size calculation...")
    try:
        from PIL import Image

        img = Image.open(working_input)
        canvas_size = img.size
        print(f"   ✓ Canvas size calculated: {canvas_size} (type: {type(canvas_size)})")

        # Test the delaunay plugin directly
        try:
            import geometry_plugins.delaunay as delaunay_plugin

            print("   ✓ Delaunay plugin imported")

            # Check if it has a generate function
            if hasattr(delaunay_plugin, "generate"):
                print("   ✓ Found generate function")

                # Try to call it and see what happens
                print(f"   → Testing delaunay.generate with canvas_size={canvas_size}")
                try:
                    shapes = delaunay_plugin.generate(
                        canvas_size=canvas_size, points=50, seed=1
                    )
                    print(
                        f"   ✓ Delaunay generate succeeded, returned {len(shapes)} shapes"
                    )
                except Exception as e:
                    print(f"   ✗ Delaunay generate failed: {e}")
                    print(
                        "   → This is likely the canvas size contract issue mentioned in handoff"
                    )

                    # Try different formats
                    for test_format in [
                        (canvas_size[0], canvas_size[1]),
                        list(canvas_size),
                        canvas_size,
                    ]:
                        try:
                            print(
                                f"   → Trying canvas_size format: {test_format} (type: {type(test_format)})"
                            )
                            shapes = delaunay_plugin.generate(
                                canvas_size=test_format, points=50, seed=1
                            )
                            print(f"   ✓ Success with format {type(test_format)}")
                            break
                        except Exception as e2:
                            print(f"   ✗ Failed with {type(test_format)}: {e2}")
            else:
                print("   ✗ No generate function found in delaunay plugin")

        except Exception as e:
            print(f"   ✗ Delaunay plugin test failed: {e}")

    except Exception as e:
        print(f"   ✗ Canvas size test failed: {e}")

    # Step 4: Test the full pipeline
    print("\n4. Testing full pipeline...")

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    test_cases = [
        {
            "name": "Direct API call",
            "func": lambda: run_cubist(
                input=working_input,
                output="output/diagnostic_api_test",
                geometry="delaunay",
                points=50,
                seed=1,
                export_svg=True,
                quiet=True,
            ),
        },
        {
            "name": "CLI pipeline call",
            "func": lambda: run_pipeline(
                input=working_input,
                output="output/diagnostic_cli_test",
                geometry="delaunay",
                points=50,
                seed=1,
                export_svg=True,
                quiet=True,
            ),
        },
    ]

    for test_case in test_cases:
        print(f"\n   Testing {test_case['name']}...")
        try:
            result = test_case["func"]()
            print(f"   ✓ {test_case['name']} completed")
            if isinstance(result, dict):
                print(f"   → Result keys: {list(result.keys())}")
                if "svg_exists" in result:
                    print(f"   → SVG exists: {result['svg_exists']}")
                if "svg_path" in result:
                    print(f"   → SVG path: {result['svg_path']}")
                    if result.get("svg_path") and Path(result["svg_path"]).exists():
                        print("   ✓ SVG file was created!")
                        # Check file size
                        svg_size = Path(result["svg_path"]).stat().st_size
                        print(f"   → SVG file size: {svg_size} bytes")
                    else:
                        print("   ✗ SVG file not found at expected path")

        except Exception as e:
            print(f"   ✗ {test_case['name']} failed: {e}")
            print(f"   → Error type: {type(e).__name__}")
            traceback.print_exc()

    # Step 5: Check what files were actually created
    print("\n5. Checking output directory...")
    output_dir = Path("output")
    if output_dir.exists():
        files = list(output_dir.iterdir())
        print(f"   Found {len(files)} files in output/:")
        for file in files:
            print(f"   - {file.name} ({file.stat().st_size} bytes)")
    else:
        print("   ✗ Output directory doesn't exist")

    # Step 6: Test SVG export fallback directly
    print("\n6. Testing SVG export fallback...")
    try:
        # Test the svg_export module directly
        test_shapes = [
            {"type": "triangle", "points": [(100, 100), (200, 100), (150, 200)]},
            {
                "type": "polygon",
                "points": [(250, 100), (350, 100), (350, 200), (250, 200)],
            },
        ]

        svg_content = svg_export.export_svg(test_shapes, width=400, height=300)
        print(
            f"   ✓ SVG export fallback works, generated {len(svg_content)} characters"
        )

        # Write test SVG
        test_svg_path = "output/diagnostic_fallback_test.svg"
        with open(test_svg_path, "w") as f:
            f.write(svg_content)
        print(f"   ✓ Test SVG written to {test_svg_path}")

    except Exception as e:
        print(f"   ✗ SVG export fallback failed: {e}")
        traceback.print_exc()

    print("\n=== Diagnostic Complete ===")
    print("Please share this output so I can help identify the issue!")
    return True


if __name__ == "__main__":
    main()
