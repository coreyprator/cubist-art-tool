import re
from pathlib import Path


def analyze_corruption_sources():
    """Find where 4000 -> 1000 parameter corruption happens"""

    project_root = Path(__file__).parent.parent

    print("=== PARAMETER CORRUPTION BUG HUNT ===")
    print(f"Project root: {project_root}")

    # Files to check for parameter corruption
    suspect_files = [
        "cubist_cli.py",
        "geometry_plugins/scatter_circles.py",
        "svg_export.py",
        "cubist_core_logic.py",
    ]

    corruption_patterns = [
        r"1000",  # hardcoded 1000 values
        r"min\(\s*\w+\s*,\s*1000\s*\)",  # min(points, 1000)
        r"points.*=.*1000",  # points assignment with 1000
        r"total_points.*1000",  # total_points with 1000
        r"if.*points.*>\s*1000",  # points > 1000 checks
        r"fallback",  # fallback mechanisms
        r"limit.*point",  # point limiting
        r"reduce.*point",  # point reduction
    ]

    print("\n🔍 SCANNING FOR CORRUPTION PATTERNS:")

    for file_path in suspect_files:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"❌ {file_path} - File not found")
            continue

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            print(f"\n📁 {file_path}:")
            found_issues = False

            for i, line in enumerate(lines, 1):
                for pattern in corruption_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        found_issues = True
                        print(f"  🚨 Line {i:3d}: {line.strip()}")

            if not found_issues:
                print("  ✅ No obvious corruption patterns found")

        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")

    # Look for specific CLI argument processing issues
    print("\n🔍 CHECKING CLI ARGUMENT PROCESSING:")

    cli_path = project_root / "cubist_cli.py"
    if cli_path.exists():
        with open(cli_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for where args.points gets processed
        points_processing = re.findall(r".*args\.points.*", content, re.IGNORECASE)
        for match in points_processing:
            print(f"  📋 args.points usage: {match.strip()}")

        # Look for parameter validation/limits
        validation_patterns = [
            r".*points.*min.*",
            r".*points.*max.*",
            r".*points.*limit.*",
            r".*points.*clip.*",
            r".*points.*constrain.*",
        ]

        for pattern in validation_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                print(f"  ⚠️  Validation: {match.strip()}")

    print("\n🎯 RECOMMENDED FIXES:")
    print("1. Search cubist_cli.py for 'min(points, 1000)' or similar limits")
    print("2. Check scatter_circles.py for hardcoded 1000 in sampling")
    print("3. Look for fallback logic that reduces point count")
    print("4. Verify --points argument parsing doesn't get overridden")
    print("5. Check if memory/performance limits cap points at 1000")


if __name__ == "__main__":
    analyze_corruption_sources()
