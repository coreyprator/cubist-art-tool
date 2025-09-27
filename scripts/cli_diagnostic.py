#!/usr/bin/env python3
"""
Diagnostic script to debug GUI→CLI interface issues
"""

import subprocess
import sys
import json


def test_cli_call(geometry, points=500, input_image="input/x_your_input_image.jpg"):
    """Test a single CLI call and capture detailed output"""

    output_path = f"output/debug_{geometry}"

    # This should match what the GUI is sending
    cmd = [
        sys.executable,
        "cubist_cli.py",
        "--input",
        input_image,
        "--output",
        output_path,
        "--geometry",
        geometry,
        "--points",
        str(points),
        "--seed",
        "42",
        "--export-svg",
    ]

    print(f"\n=== Testing {geometry} ===")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=".",
            timeout=120,  # 2 minute timeout
        )

        print(f"Return code: {result.returncode}")

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        # Try to parse the JSON output if successful
        if result.returncode == 0:
            try:
                output_lines = result.stdout.strip().split("\n")
                json_line = output_lines[-1]  # Last line should be JSON
                data = json.loads(json_line)
                print(
                    f"✅ Success: {data.get('svg_shapes', 0)} shapes, {data.get('svg_size', 0)} bytes"
                )
            except:
                print("⚠️ Success but couldn't parse JSON output")
        else:
            print(f"❌ Failed with rc={result.returncode}")

    except subprocess.TimeoutExpired:
        print("❌ Command timed out (>2 minutes)")
    except Exception as e:
        print(f"❌ Exception: {e}")


def main():
    print("=== CLI Diagnostic Tool ===")
    print("Testing individual geometry CLI calls to debug GUI failures...\n")

    # Test the failing geometries first
    failing_geometries = ["delaunay", "rectangles", "poisson_disk"]
    working_geometries = ["voronoi", "scatter_circles", "concentric_circles"]

    print("🔍 Testing FAILING geometries:")
    for geom in failing_geometries:
        test_cli_call(geom)

    print("\n🔍 Testing WORKING geometries:")
    for geom in working_geometries:
        test_cli_call(geom)

    print("\n=== Diagnostic Complete ===")
    print("Check the outputs above to identify:")
    print("1. Exact error messages for failing geometries")
    print("2. Whether input image is being processed correctly")
    print("3. CLI argument format compatibility")


if __name__ == "__main__":
    main()
