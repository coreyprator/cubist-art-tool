#!/usr/bin/env python3
"""
Check for existing UI components in the cubist_art project
and prepare runui integration
"""

from pathlib import Path
import json


def main():
    print("=== Cubist Art UI Component Discovery ===")

    # Check current directory structure
    cwd = Path.cwd()
    print(f"Project root: {cwd}")

    # Look for existing UI files
    ui_files = [
        "app.py",
        "ui_app.py",
        "web_gallery.py",
        "gallery.py",
        "viewer.py",
        "server.py",
        "ui.py",
    ]

    print("\n1. Checking for existing UI components...")
    found_ui = []
    for ui_file in ui_files:
        if Path(ui_file).exists():
            size = Path(ui_file).stat().st_size
            print(f"   ✓ Found {ui_file} ({size} bytes)")
            found_ui.append(ui_file)
        else:
            print(f"   - Missing {ui_file}")

    # Check for directories with UI components
    ui_dirs = ["ui", "web", "gallery", "viewer", "app", "gui"]
    print("\n2. Checking for UI directories...")
    found_dirs = []
    for ui_dir in ui_dirs:
        if Path(ui_dir).is_dir():
            files = list(Path(ui_dir).glob("*"))
            print(f"   ✓ Found directory {ui_dir}/ with {len(files)} files")
            found_dirs.append(ui_dir)
        else:
            print(f"   - Missing {ui_dir}/")

    # Check for existing runui configuration
    print("\n3. Checking for runui configuration...")
    pf_dir = Path(".pf")
    runui_config = pf_dir / "runui.json"

    if runui_config.exists():
        print(f"   ✓ Found {runui_config}")
        try:
            with open(runui_config) as f:
                config = json.load(f)
            print(f"   → Current config: {config}")
        except Exception as e:
            print(f"   ✗ Error reading config: {e}")
    else:
        print(f"   - Missing {runui_config}")
        if not pf_dir.exists():
            print("   - Missing .pf/ directory")

    # Check output directories for SVG files
    print("\n4. Checking for generated SVGs...")
    output_dir = Path("output")
    if output_dir.exists():
        svg_files = list(output_dir.glob("**/*.svg"))
        print(f"   ✓ Found {len(svg_files)} SVG files in output/")

        # Show recent SVGs
        if svg_files:
            recent_svgs = sorted(
                svg_files, key=lambda p: p.stat().st_mtime, reverse=True
            )[:5]
            print("   Recent SVGs:")
            for svg in recent_svgs:
                size = svg.stat().st_size
                print(f"     - {svg} ({size} bytes)")
    else:
        print("   - No output/ directory found")

    # Check for web-related dependencies
    print("\n5. Checking for web dependencies...")
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        requirements = requirements_file.read_text()
        web_libs = [
            "flask",
            "fastapi",
            "django",
            "tornado",
            "bottle",
            "cherrypy",
            "http.server",
        ]
        found_web_libs = [lib for lib in web_libs if lib in requirements.lower()]
        if found_web_libs:
            print(f"   ✓ Found web libraries: {', '.join(found_web_libs)}")
        else:
            print("   - No web libraries found in requirements.txt")

    # Generate recommendations
    print("\n=== Recommendations ===")

    if found_ui:
        print("✓ Existing UI components found - need to integrate with runui")
    else:
        print("○ No existing UI - will create web gallery from scratch")

    if not runui_config.exists():
        print("○ Need to create .pf/runui.json configuration")

    if output_dir.exists() and svg_files:
        print(f"✓ {len(svg_files)} SVG files available for gallery display")
    else:
        print("○ Generate some SVGs first using the production script")

    print("\nNext steps:")
    print("1. Create .pf/runui.json manifest")
    print("2. Create web gallery UI")
    print("3. Test runui integration")


if __name__ == "__main__":
    main()
