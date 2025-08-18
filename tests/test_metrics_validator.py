import json
import os
import tempfile
import sys
import subprocess

def test_cli_metrics_smoke():
    # Use a tiny input image from input/ or generate a small one on the fly
    # Run the CLI with --export-svg --metrics-json
    # Assert file existence and that shape_count > 0 for svg when geometry_mode != rectangles cap
    assert True  # fill once CLI is stable
