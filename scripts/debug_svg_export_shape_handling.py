import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=== SVG EXPORT SHAPE HANDLING DEBUG ===")

try:
    import svg_export
    import inspect

    # Get the source code to see how it processes shapes
    source = inspect.getsource(svg_export.export_svg)
    lines = source.split("\n")

    print("🔍 Analyzing svg_export.export_svg shape processing logic...")
    for i, line in enumerate(lines, 1):
        if "shape" in line.lower() and any(
            keyword in line.lower()
            for keyword in ["type", "circle", "rect", "polygon", "if", "for"]
        ):
            print(f"   Line {i}: {line.strip()}")

    # Test with our exact dict format
    test_shapes = [
        {
            "type": "circle",
            "cx": 50.0,
            "cy": 50.0,
            "r": 10.0,
            "fill": "black",
            "stroke": "none",
        },
        {
            "type": "circle",
            "cx": 25.0,
            "cy": 75.0,
            "r": 15.0,
            "fill": "red",
            "stroke": "blue",
        },
    ]

    print(f"\n🧪 Testing with {len(test_shapes)} test shapes...")
    print(f"   First shape: {test_shapes[0]}")

    result = svg_export.export_svg(test_shapes, width=100, height=100)
    circle_count = result.count("<circle")

    print(f"   Result contains {circle_count} <circle elements")
    print(f"   Expected: {len(test_shapes)} circles")

    if circle_count == 0:
        print(
            "\n❌ PROBLEM: svg_export.export_svg is not processing dict shapes correctly!"
        )
        print("   The function expects a different shape format")

        # Show a snippet of the result
        print("\n📋 SVG result sample:")
        print(result[:300] + "..." if len(result) > 300 else result)

    else:
        print("✅ SUCCESS: svg_export.export_svg processed shapes correctly")

except Exception as e:
    print(f"❌ Debug failed: {e}")
    import traceback

    traceback.print_exc()

print("\n🎯 ACTION NEEDED:")
print(
    "The svg_export.export_svg function needs to be updated to handle dict format shapes"
)
print("It's currently expecting a different format and ignoring our circle dicts")
