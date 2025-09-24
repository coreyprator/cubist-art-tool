#!/usr/bin/env python3
"""
Quick fix for cubist_cli.py syntax error on line 161
"""

import re
from pathlib import Path


def fix_cubist_cli():
    """Fix the escaped docstring syntax error in cubist_cli.py"""

    cli_file = Path("cubist_cli.py")
    if not cli_file.exists():
        print("Error: cubist_cli.py not found")
        return False

    # Read the file
    content = cli_file.read_text(encoding="utf-8")

    # Fix the problematic line - replace escaped quotes with normal quotes
    # The error is: \"\"\"Adapter-friendly pipeline...\"\"\"
    # Should be: """Adapter-friendly pipeline..."""

    fixed_content = re.sub(r'\\"\\"\\"([^"]+)\\"\\"\\"', r'"""\1"""', content)

    # Also fix any other escaped triple quotes
    fixed_content = fixed_content.replace('\\"\\"\\"', '"""')

    # Write back the fixed content
    cli_file.write_text(fixed_content, encoding="utf-8")

    print("Fixed syntax error in cubist_cli.py")
    return True


if __name__ == "__main__":
    fix_cubist_cli()
