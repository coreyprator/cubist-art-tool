import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=== SHAPE FORMAT MISMATCH DEBUG ===")

try:
    # Load scatter_circles plugin
    import geometry_plugins.scatter_circles as sc
    import svg_export

    print("🔍 Testing shape generation and format...")

    # Generate shapes with small count for easier debugging
    canvas_size = (100, 100)
    test_points = 5

    shapes = sc.generate(canvas_size, test_points, seed=42)

    print(f"✅ Generated shapes: {type(shapes)}")
    print(f"✅ Shape count: {len(shapes) if shapes else 0}")

    if shapes:
        print(f"✅ First shape: {shapes[0]}")
        print(f"✅ First shape type: {type(shapes[0])}")

        # Check if shapes are tuples (x, y, radius) or dicts
        if isinstance(shapes[0], tuple) and len(shapes[0]) == 3:
            print("🎯 FOUND THE ISSUE: Shapes are tuples (x, y, radius)")
            print("   svg_export.export_svg expects dict format with 'type' field")
            print("   Need to convert tuples to proper shape dictionaries")

            # Show what svg_export expects
            print("\n📋 Converting tuple format to dict format...")
            converted_shapes = []
            for x, y, radius in shapes[:3]:  # Convert first 3 for demo
                shape_dict = {
                    "type": "circle",
                    "cx": x,
                    "cy": y,
                    "r": radius,
                    "fill": "black",
                    "stroke": "none",
                }
                converted_shapes.append(shape_dict)
                print(f"   Tuple {(x, y, radius)} → Dict {shape_dict}")

            # Test SVG export with converted format
            print("\n🧪 Testing SVG export with converted shapes...")
            try:
                svg_content = svg_export.export_svg(
                    converted_shapes, width=100, height=100
                )
                circle_count = svg_content.count("<circle")
                print("✅ SVG export successful!")
                print(f"✅ Circle elements in SVG: {circle_count}")
                print(f"✅ SVG length: {len(svg_content)} characters")

                if circle_count > 0:
                    print("🎯 CONFIRMED: Format conversion fixes the issue!")
                else:
                    print("❌ Still no circles - different issue")

            except Exception as e:
                print(f"❌ SVG export still failed: {e}")

        elif isinstance(shapes[0], dict):
            print("✅ Shapes are already in dict format")
            # Check if they have the right fields
            required_fields = ["type"]
            missing_fields = [f for f in required_fields if f not in shapes[0]]
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
            else:
                print("✅ Shape format looks correct")
        else:
            print(f"❌ Unexpected shape format: {type(shapes[0])}")
    else:
        print("❌ No shapes generated!")

    # Check the actual scatter_circles.generate function to see what it returns
    print("\n🔍 Checking scatter_circles.generate function...")
    import inspect

    source = inspect.getsource(sc.generate)
    lines = source.split("\n")

    for i, line in enumerate(lines):
        if "return" in line:
            print(f"  Line {i}: {line.strip()}")

    # Look for the scatter_circles function that generate() calls
    if hasattr(sc, "scatter_circles"):
        print("\n🔍 Checking scatter_circles function...")
        source2 = inspect.getsource(sc.scatter_circles)
        lines2 = source2.split("\n")

        for i, line in enumerate(lines2):
            if "return" in line or "circles.append" in line or "circle" in line.lower():
                print(f"  Line {i}: {line.strip()}")

except Exception as e:
    print(f"❌ Debug failed: {e}")
    import traceback

    traceback.print_exc()

print("\n🎯 RECOMMENDED FIX:")
print("1. Update scatter_circles.generate() to return dict format instead of tuples")
print(
    "2. Convert (x, y, radius) tuples to {'type': 'circle', 'cx': x, 'cy': y, 'r': radius}"
)
print("3. Or update svg_export.export_svg() to handle tuple format")
print("4. Test with small point count first, then scale up")
