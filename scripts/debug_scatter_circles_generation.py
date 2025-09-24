# Debug scatter_circles shape generation issue
import sys
import os
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=== SCATTER_CIRCLES SHAPE GENERATION DEBUG ===")


def test_scatter_circles_directly():
    print("\n🔍 Testing scatter_circles plugin directly...")

    try:
        import geometry_plugins.scatter_circles as scatter

        canvas_size = (3024, 4032)
        total_points = 4000
        seed = 42

        print(
            f"Calling scatter_circles.generate({canvas_size}, {total_points}, seed={seed})"
        )
        shapes = scatter.generate(canvas_size, total_points, seed=seed)

        print(f"✅ Plugin returned: {type(shapes)}")
        print(
            f"✅ Shape count: {len(shapes) if shapes and hasattr(shapes, '__len__') else 'unknown'}"
        )

        if shapes:
            if hasattr(shapes, "__len__") and len(shapes) > 0:
                print(
                    f"✅ First shape sample: {shapes[0] if len(shapes) > 0 else 'none'}"
                )

                # Analyze shape structure
                if len(shapes) > 0:
                    first_shape = shapes[0]
                    print(f"✅ First shape type: {type(first_shape)}")
                    if isinstance(first_shape, dict):
                        print(f"✅ First shape keys: {list(first_shape.keys())}")
                        if "type" in first_shape:
                            print(f"✅ Shape type: {first_shape['type']}")
                        if "cx" in first_shape and "cy" in first_shape:
                            print(
                                f"✅ Circle center: ({first_shape.get('cx', 'unknown')}, {first_shape.get('cy', 'unknown')})"
                            )
                        if "r" in first_shape:
                            print(
                                f"✅ Circle radius: {first_shape.get('r', 'unknown')}"
                            )

            # Test if shapes are empty or malformed
            if hasattr(shapes, "__len__"):
                if len(shapes) == 0:
                    print("❌ PROBLEM: Plugin returned empty list!")
                elif len(shapes) < total_points // 4:
                    print(
                        f"⚠️ WARNING: Only {len(shapes)} shapes, expected ~{total_points}"
                    )
                else:
                    print(f"✅ Shape count looks reasonable: {len(shapes)}")
            else:
                print("❌ PROBLEM: Shapes object has no length!")

        else:
            print("❌ PROBLEM: Plugin returned None or falsy value!")

        return shapes

    except Exception as e:
        print(f"❌ Plugin test failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_svg_export_fallback(shapes):
    print("\n🔍 Testing SVG export process...")

    if not shapes:
        print("❌ No shapes to export")
        return

    try:
        import svg_export

        canvas_size = (3024, 4032)

        print(
            f"Calling svg_export.export_svg(shapes, width={canvas_size[0]}, height={canvas_size[1]})"
        )
        svg_content = svg_export.export_svg(
            shapes, width=canvas_size[0], height=canvas_size[1]
        )

        print("✅ SVG export succeeded")
        print(f"✅ SVG content length: {len(svg_content)} characters")

        # Analyze SVG content
        if "<circle" in svg_content:
            circle_count = svg_content.count("<circle")
            print(f"✅ SVG contains {circle_count} circle elements")
            if circle_count < len(shapes) // 2:
                print("⚠️ WARNING: Fewer SVG circles than input shapes")
        else:
            print("❌ PROBLEM: No circle elements found in SVG!")

        # Show sample SVG content
        if len(svg_content) > 100:
            print(f"SVG sample: {svg_content[:200]}...")
        else:
            print(f"Full SVG: {svg_content}")

    except Exception as e:
        print(f"❌ SVG export failed: {e}")
        import traceback

        traceback.print_exc()


def analyze_plugin_source():
    print("\n🔍 Analyzing scatter_circles plugin source...")

    plugin_path = Path(project_root) / "geometry_plugins" / "scatter_circles.py"
    if plugin_path.exists():
        try:
            source = plugin_path.read_text()
            lines = source.splitlines()

            print(f"✅ Plugin file: {len(lines)} lines")

            # Look for generate function
            generate_lines = []
            for i, line in enumerate(lines, 1):
                if "def generate(" in line:
                    generate_lines.append((i, line.strip()))
                elif "return" in line and i > 100:  # Likely in generate function
                    generate_lines.append((i, line.strip()))

            print("Generate function lines:")
            for line_num, line in generate_lines:
                print(f"  Line {line_num}: {line}")

            # Look for potential issues
            if "return []" in source:
                print(
                    "⚠️ WARNING: Plugin contains 'return []' - might return empty list"
                )
            if "return None" in source:
                print("⚠️ WARNING: Plugin contains 'return None'")

        except Exception as e:
            print(f"❌ Failed to analyze plugin source: {e}")
    else:
        print(f"❌ Plugin file not found: {plugin_path}")


# Run the debug tests
if __name__ == "__main__":
    shapes = test_scatter_circles_directly()
    test_svg_export_fallback(shapes)
    analyze_plugin_source()

    print(f"\n{'='*60}")
    print("SHAPE GENERATION ANALYSIS SUMMARY")
    print(f"{'='*60}")

    print("🎯 Key Findings:")
    print("1. Parameter fix works - plugin receives total_points=4000")
    print("2. Plugin generates sampling data correctly")
    print("3. BUT: Final SVG only has 1 shape instead of 4000")
    print("4. SVG export fallback activates with 'exported 0 shapes'")

    print("\n💡 Most Likely Issues:")
    print("1. scatter_circles.generate() returns empty list or None")
    print("2. Shape objects are malformed and svg_export can't process them")
    print("3. Exception in generate() causes fallback to empty result")
    print("4. Plugin generates samples but fails to create shape objects")

    print("\n🔧 Next Steps:")
    print("1. Check if scatter_circles.generate() actually returns shapes")
    print("2. Verify shape object structure matches svg_export expectations")
    print("3. Look for exceptions in the generate() function")
    print("4. Test with smaller point counts to isolate the issue")
