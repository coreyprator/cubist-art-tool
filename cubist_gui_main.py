#!/usr/bin/env python3
"""
Cubist GUI Main Entry Point
Redirects to the proper production UI
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Launch the production UI"""
    print("🎨 Launching Cubist Art Production UI...")

    # Check if prod_ui.py exists
    prod_ui = Path("tools/prod_ui.py")
    if not prod_ui.exists():
        print(f"Error: {prod_ui} not found")
        sys.exit(1)

    # Launch the production UI
    try:
        subprocess.run([sys.executable, str(prod_ui)])
    except KeyboardInterrupt:
        print("\nUI stopped by user")
    except Exception as e:
        print(f"Error launching UI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
