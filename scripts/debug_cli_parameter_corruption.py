# Debug CLI parameter corruption (4000 → 1000)
import sys
import os
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=== CLI PARAMETER CORRUPTION DEBUG ===")

# First, let's examine the CLI code structure
cli_path = Path(project_root) / "cubist_cli.py"
if cli_path.exists():
    print(f"✅ Found CLI: {cli_path}")

    # Read the CLI source code to find parameter passing logic
    try:
        cli_source = cli_path.read_text()

        print("\n🔍 CLI Source Analysis:")
        print(f"  File size: {len(cli_source)} characters")
        print(f"  Lines: {len(cli_source.splitlines())}")

        # Look for parameter passing patterns
        lines = cli_source.splitlines()
        param_lines = []

        for i, line in enumerate(lines, 1):
            if any(
                keyword in line.lower()
                for keyword in [
                    "total_points",
                    "points",
                    "generate(",
                    "plugin.generate",
                ]
            ):
                param_lines.append((i, line.strip()))

        print(f"\n📊 Parameter-related lines found: {len(param_lines)}")
        for line_num, line in param_lines:
            print(f"  Line {line_num:3d}: {line}")

            # Check for suspicious parameter modifications
            if "total_points" in line and (
                "1000" in line or "min(" in line or "max(" in line
            ):
                print("    ⚠️  SUSPICIOUS: Potential parameter modification!")

        # Look for the specific pattern that might cause 4000 → 1000
        print("\n🎯 Looking for parameter corruption patterns...")

        corruption_patterns = [
            "1000",
            "min(",
            "max(",
            "total_points",
            "// 4",
            "/ 4",
            "limit",
            "clamp",
        ]

        for pattern in corruption_patterns:
            if pattern in cli_source:
                print(f"  Found pattern '{pattern}' in CLI source")

        # Look for the scatter_circles trace that showed total_points=1000
        if "scatter_circles" in cli_source or "trace" in cli_source:
            print("  ✅ CLI contains scatter_circles or trace logic")

    except Exception as e:
        print(f"❌ Failed to read CLI source: {e}")
else:
    print(f"❌ CLI not found: {cli_path}")

# Now let's test direct plugin calls vs CLI calls to isolate the bug
print(f"\n{'='*60}")
print("DIRECT PLUGIN vs CLI COMPARISON")
print(f"{'='*60}")


def test_direct_plugin():
    print("\n🔍 Testing DIRECT plugin call...")
    try:
        import geometry_plugins.scatter_circles as scatter

        canvas_size = (3024, 4032)
        total_points = 4000

        shapes = scatter.generate(canvas_size, total_points, seed=42)
        print(f"  Direct call result: {len(shapes) if shapes else 0} shapes")
        print(
            f"  Parameters passed: canvas_size={canvas_size}, total_points={total_points}"
        )

        if len(shapes) > 3000:
            print("  ✅ Direct plugin works correctly")
        else:
            print("  ❌ Direct plugin also broken")

        return len(shapes)

    except Exception as e:
        print(f"  ❌ Direct plugin failed: {e}")
        import traceback

        traceback.print_exc()
        return 0


def analyze_cli_logic():
    print("\n🔍 Analyzing CLI parameter passing logic...")
    try:
        # Import CLI module to examine its functions
        if cli_path.exists():
            spec = importlib.util.spec_from_file_location("cli_module", cli_path)
            cli_module = importlib.util.module_from_spec(spec)

            # Look for main function and parameter handling
            if hasattr(cli_module, "main"):
                print("  ✅ CLI has main() function")

            # Check for any parameter processing functions
            cli_attrs = dir(cli_module)
            param_funcs = [attr for attr in cli_attrs if "param" in attr.lower()]
            if param_funcs:
                print(f"  Parameter-related functions: {param_funcs}")

    except Exception as e:
        print(f"  ❌ Failed to analyze CLI: {e}")


# Run the tests
import importlib.util

direct_shapes = test_direct_plugin()
analyze_cli_logic()

print(f"\n{'='*60}")
print("CORRUPTION ANALYSIS SUMMARY")
print(f"{'='*60}")

print("🎯 Key Findings:")
print("1. CLI debug shows total_points=1000 (should be 4000)")
print(f"2. Direct plugin test shows: {direct_shapes} shapes")
print("3. CLI fallback mechanism: 'SVG export fallback: exported X shapes'")

print("\n💡 Next Steps:")
print("1. Find exact line where 4000 → 1000 happens")
print("2. Find why SVG export fallback activates")
print("3. Compare CLI parameter passing vs direct calls")
print("4. Fix the parameter corruption bug")

print("\n🚨 Most Likely Bug Locations:")
print("- Parameter validation/limiting code")
print("- Memory/performance limits in CLI")
print("- Error handling that reduces points")
print("- Fallback algorithms with hardcoded limits")
