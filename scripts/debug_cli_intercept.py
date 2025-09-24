# Debug the CLI layer that the GUI calls
import sys
import os
import json
import subprocess

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=== CLI LAYER DEBUG ===")


# Simulate the exact CLI calls that the GUI makes
def test_cli_call(geometry, points=4000, seed=42):
    print(f"\n🔍 Testing CLI call for {geometry.upper()}")

    cli_cmd = [
        sys.executable,
        "cubist_cli.py",
        "--input",
        "G:/My Drive/Code/Python/cubist_art/input/x_your_input_image.jpg",
        "--output",
        f"output/debug_cli_{geometry}",
        "--geometry",
        geometry,
        "--points",
        str(points),
        "--seed",
        str(seed),
        "--export-svg",
    ]

    print(f"Command: {' '.join(cli_cmd)}")

    try:
        # Run the CLI command and capture output
        result = subprocess.run(
            cli_cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
        )

        print(f"Return code: {result.returncode}")
        print(f"STDOUT length: {len(result.stdout)} chars")
        print(f"STDERR length: {len(result.stderr)} chars")

        if result.stdout.strip():
            print("STDOUT sample:")
            print(
                result.stdout[:500] + "..."
                if len(result.stdout) > 500
                else result.stdout
            )

            # Try to parse JSON output if it exists
            try:
                if "{" in result.stdout and "}" in result.stdout:
                    json_start = result.stdout.find("{")
                    json_end = result.stdout.rfind("}") + 1
                    json_str = result.stdout[json_start:json_end]
                    json_data = json.loads(json_str)

                    print("\n📊 PARSED JSON RESULTS:")
                    print(f"  RC: {json_data.get('rc', 'unknown')}")
                    print(
                        f"  Shapes: {json_data.get('outputs', {}).get('svg_shapes', 'unknown')}"
                    )
                    print(
                        f"  SVG Size: {json_data.get('outputs', {}).get('svg_size', 'unknown')} bytes"
                    )
                    print(f"  Time: {json_data.get('elapsed_s', 'unknown')}s")

                    if json_data.get("outputs", {}).get("svg_shapes", 0) < 100:
                        print("  ❌ PROBLEM: Very few shapes generated!")
                    elif (
                        json_data.get("outputs", {}).get("svg_shapes", 0) < points // 4
                    ):
                        print("  ⚠️  WARNING: Fewer shapes than expected")
                    else:
                        print("  ✅ Shape count looks reasonable")

            except Exception as e:
                print(f"Failed to parse JSON: {e}")

        if result.stderr.strip():
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0, result

    except subprocess.TimeoutExpired:
        print("❌ Command timed out (120s)")
        return False, None
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return False, None


# Test the failing geometries from your log
geometries_to_test = [
    ("delaunay", 496),  # Expected vs actual shapes
    ("voronoi", 1),
    ("rectangles", 65),
    ("scatter_circles", 1),
    ("concentric_circles", 1),
]

print("Testing the exact CLI calls that GUI makes...")
print("This will show us what's different between GUI→CLI vs Direct Plugin calls")

results = {}
for geometry, expected_shapes in geometries_to_test:
    success, result = test_cli_call(geometry, points=4000, seed=42)
    results[geometry] = {"success": success, "expected_shapes": expected_shapes}

    if not success:
        print(f"❌ {geometry} CLI call failed - this might be the bug!")

    print("-" * 60)

print(f"\n{'='*60}")
print("CLI DEBUG SUMMARY")
print(f"{'='*60}")

failed_count = sum(1 for r in results.values() if not r["success"])
if failed_count > 0:
    print(f"❌ {failed_count} CLI calls failed - this explains the GUI failures!")
else:
    print("✅ All CLI calls succeeded - the bug might be in parameter passing")

print("\n💡 Next Steps:")
print("1. Check if CLI calls match direct plugin performance")
print("2. Look for error handling/fallback code in cubist_cli.py")
print("3. Compare CLI vs direct plugin parameter passing")
print("4. Check for preprocessing issues in CLI layer")

print("\n🎯 Expected Discovery:")
print("- CLI layer has parameter passing bugs")
print("- Error handling returns fallback shapes")
print("- Different plugin loading mechanism")
print("- Image preprocessing issues in CLI")
