import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=== CLI SVG EXPORT PATH DEBUG ===")

# Check what svg_export.export_svg actually expects
try:
    import svg_export
    import inspect

    print("🔍 Checking svg_export.export_svg function signature...")
    sig = inspect.signature(svg_export.export_svg)
    print(f"   Signature: {sig}")

    # Check the source code for the "exported 0 shapes" message
    source = inspect.getsource(svg_export.export_svg)
    print("\n📋 Looking for 'exported 0 shapes' in svg_export.export_svg...")

    lines = source.split("\n")
    for i, line in enumerate(lines, 1):
        if "exported" in line.lower() and ("0" in line or "fallback" in line.lower()):
            print(f"   Line {i}: {line.strip()}")

    # Test what svg_export.export_svg actually does with dict format
    print("\n🧪 Testing svg_export.export_svg with dict format...")
    test_shapes = [
        {
            "type": "circle",
            "cx": 50.0,
            "cy": 50.0,
            "r": 10.0,
            "fill": "black",
            "stroke": "none",
        }
    ]

    try:
        result = svg_export.export_svg(test_shapes, width=100, height=100)
        print("   ✅ svg_export.export_svg succeeded")
        print(f"   ✅ Result length: {len(result)} chars")
        print(f"   ✅ Contains <circle: {'<circle' in result}")
        if "<circle" not in result:
            print(f"   ❌ Result content: {result[:200]}...")
    except Exception as e:
        print(f"   ❌ svg_export.export_svg failed: {e}")
        import traceback

        traceback.print_exc()

except Exception as e:
    print(f"❌ Could not import svg_export: {e}")

# Check if cubist_cli.py is calling the right exporter
print("\n🔍 Checking how cubist_cli.py calls svg_export...")
try:
    cli_path = project_root / "cubist_cli.py"
    with open(cli_path, "r", encoding="utf-8") as f:
        cli_content = f.read()

    # Look for svg export calls
    lines = cli_content.split("\n")
    for i, line in enumerate(lines, 1):
        if "svg_export" in line or "export_svg" in line:
            print(f"   Line {i}: {line.strip()}")

    # Look for the fallback message
    for i, line in enumerate(lines, 1):
        if "fallback" in line.lower() and "export" in line.lower():
            print(f"   FALLBACK Line {i}: {line.strip()}")

except Exception as e:
    print(f"❌ Could not read cubist_cli.py: {e}")

print("\n🎯 DIAGNOSIS:")
print("1. Check if svg_export.export_svg expects different parameters")
print("2. Find where 'SVG export fallback: exported 0 shapes' comes from")
print("3. Verify the CLI is calling the right export function")
print("4. Check if there's parameter mismatch in the export call")
