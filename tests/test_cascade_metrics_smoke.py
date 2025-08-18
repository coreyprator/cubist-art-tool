import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image

def run_cmd(args):
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.returncode == 0, f"CLI failed:\n{proc.stdout}"
    return proc

def make_img(p):
    img = Image.new("RGB", (64, 64), (128, 128, 128))
    img.save(p)

def test_cascade_determinism_and_metrics():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        in_png = td / "in.png"
        make_img(in_png)
        out_svg1 = td / "out1.svg"
        out_svg2 = td / "out2.svg"
        m1 = td / "m1.json"
        m2 = td / "m2.json"
        cli = sys.executable
        cli_path = os.path.join(os.path.dirname(__file__), "..", "cubist_cli.py")
        cli_path = os.path.abspath(cli_path)
        cmd_base = [
            cli, cli_path,
            "--input", str(in_png),
            "--points", "50",
            "--geometry", "delaunay",
            "--export-svg",
            "--metrics-json", str(m1),
            "--cascade-stages", "3",
            "--seed", "123"
        ]
        run_cmd(cmd_base)
        # run again to check determinism
        cmd2 = cmd_base.copy()
        cmd2[cmd2.index(str(m1))] = str(m2)
        run_cmd(cmd2)
        j1 = json.loads(Path(m1).read_text(encoding="utf-8"))
        j2 = json.loads(Path(m2).read_text(encoding="utf-8"))
        assert j1 == j2
        assert j1["totals"]["points"] == 50
        assert j1["totals"]["stages"] == 3
        stages = j1["stages"]
        assert len(stages) == 3
        assert [s["points"] for s in stages] == sorted([s["points"] for s in stages])  # non-decreasing
        assert stages[-1]["points"] == 50
        if stages[-1]["svg_shape_count"] is not None:
            assert stages[-1]["svg_shape_count"] > 0

        # Different seed should change the metrics json
        m3 = td / "m3.json"
        cmd3 = cmd_base.copy()
        cmd3[cmd3.index(str(m2))] = str(m3)
        cmd3[cmd3.index("--seed") + 1] = "456"
        run_cmd(cmd3)
        j3 = json.loads(Path(m3).read_text(encoding="utf-8"))
        assert j3 != j1
