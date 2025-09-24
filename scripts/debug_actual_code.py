# scripts/debug_actual_code.py - FIXED VERSION
import sys
import os
import inspect

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=== Delaunay Plugin Debug (Fixed) ===")
print(f"Project root: {project_root}")
print(f"Current working directory: {os.getcwd()}")

# 1. Check which delaunay.py is being loaded
try:
    import geometry_plugins.delaunay as d

    print(f"✓ Delaunay plugin loaded from: {inspect.getfile(d)}")

    # 2. Check if it has the generate function we expect
    if hasattr(d, "generate"):
        print("✓ generate() function found")
        sig = inspect.signature(d.generate)
        print(f"  Function signature: {sig}")
    else:
        print("✗ generate() function missing!")

    # 3. Show first 500 chars of the actual loaded code
    print("\n=== First 500 chars of loaded generate() function ===")
    try:
        source = inspect.getsource(d.generate)
        print(source[:500] + ("..." if len(source) > 500 else ""))
    except Exception as e:
        print(f"Could not get source: {e}")

    # 4. Test with your sculpture image dimensions
    print("\n=== Testing point generation with sculpture image dimensions ===")
    canvas_size = (3024, 4032)  # Your sculpture image dimensions
    test_points = 50

    try:
        shapes = d.generate(canvas_size, test_points, seed=42)
        if shapes:
            print(f"✓ Generated {len(shapes)} shapes")

            # Analyze coordinate ranges
            all_x = []
            all_y = []

            for shape in shapes[:10]:  # Check first 10 shapes
                if "points" in shape:
                    for point in shape["points"]:
                        all_x.append(point[0])
                        all_y.append(point[1])

            if all_x and all_y:
                print(
                    f"  X range: {min(all_x):.1f} - {max(all_x):.1f} (should be ~0-3024)"
                )
                print(
                    f"  Y range: {min(all_y):.1f} - {max(all_y):.1f} (should be ~0-4032)"
                )

                # Check if coordinates look reasonable
                x_range = max(all_x) - min(all_x)
                y_range = max(all_y) - min(all_y)

                print(f"  X span: {x_range:.1f} pixels")
                print(f"  Y span: {y_range:.1f} pixels")

                if x_range < 100:
                    print("⚠️  WARNING: X coordinate range is suspiciously narrow!")
                    print(
                        "    This explains why you're getting simple patterns instead of complex art"
                    )
                else:
                    print(
                        "✓ X coordinate range looks reasonable for full-image sampling"
                    )

                if y_range < 100:
                    print("⚠️  WARNING: Y coordinate range is suspiciously narrow!")
                else:
                    print("✓ Y coordinate range looks reasonable")

                # Show sample coordinates
                print(f"  Sample coordinates: {list(zip(all_x[:3], all_y[:3]))}")

            else:
                print("✗ No coordinate data found in shapes")
        else:
            print("✗ No shapes generated")

    except Exception as e:
        print(f"✗ Error testing generate(): {e}")
        import traceback

        traceback.print_exc()

    # 5. Test with different point counts to see if the issue is consistent
    print("\n=== Testing different point counts ===")
    for points in [10, 50, 200]:
        try:
            shapes = d.generate(canvas_size, points, seed=123)
            if shapes and len(shapes) > 0:
                # Get coordinate ranges
                all_x = []
                for shape in shapes[:5]:
                    if "points" in shape:
                        for point in shape["points"]:
                            all_x.append(point[0])

                if all_x:
                    x_min, x_max = min(all_x), max(all_x)
                    print(
                        f"  {points} points: X range {x_min:.1f} - {x_max:.1f} (span: {x_max-x_min:.1f})"
                    )
                else:
                    print(f"  {points} points: No coordinates found")
            else:
                print(f"  {points} points: No shapes generated")
        except Exception as e:
            print(f"  {points} points: Error - {e}")

    # 6. Check if there are multiple delaunay.py files
    print("\n=== Searching for other delaunay.py files ===")
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file == "delaunay.py":
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_root)
                print(f"  Found: {rel_path}")

except ImportError as e:
    print(f"✗ Could not import delaunay plugin: {e}")
    print(f"   Project root: {project_root}")
    print(f"   Working directory: {os.getcwd()}")
    print(f"   Python path includes: {project_root in sys.path}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback

    traceback.print_exc()

print("\n=== Analysis Complete ===")
print("Key Questions:")
print("1. Are X coordinates narrow (1-5) or full-width (0-3000+)?")
print("2. Does the coordinate range match your sculpture image dimensions?")
print("3. Is the same delaunay.py being used that we examined?")
print("\nIf coordinates are narrow, we've found the sampling bug.")
print(
    "If coordinates are full-width, the issue is in image processing or color sampling."
)
