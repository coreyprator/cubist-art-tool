#!/usr/bin/env python3
"""
Fix for canvas_size duplicate parameter issue in cubist_cli.py
"""

from pathlib import Path


def fix_canvas_size_issue():
    """Remove duplicate canvas_size parameter from generate() call"""

    cli_file = Path("cubist_cli.py")
    content = cli_file.read_text(encoding="utf-8")

    # Find and fix the line that passes canvas_size as a keyword argument
    # when it's already being passed positionally

    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        # Look for the problematic canvas_size parameter
        if "canvas_size=_canvas_size" in line and "getattr(geom_mod, cand)" in line:
            # Comment out this parameter to prevent duplication
            fixed_line = line.replace(
                "canvas_size=_canvas_size,",
                "# canvas_size=_canvas_size,  # Fixed: prevent duplicate param",
            )
            fixed_lines.append(fixed_line)
            print(f"Fixed line: {line.strip()}")
        else:
            fixed_lines.append(line)

    cli_file.write_text("\n".join(fixed_lines), encoding="utf-8")
    print("Fixed canvas_size duplicate parameter issue")


if __name__ == "__main__":
    fix_canvas_size_issue()
