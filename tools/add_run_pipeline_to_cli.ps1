[CmdletBinding()]
param([string]$File = "cubist_cli.py")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $File)) { Write-Error "Not found: $File"; exit 1 }
$text = Get-Content -Raw -Encoding UTF8 $File
if ($text -match '(?ms)^\s*def\s+run_pipeline\s*\(') { Write-Host "run_pipeline already present in $File"; exit 0 }

$fn = @"
# Programmatic entrypoint mirroring CLI main(); returns info dict.
def run_pipeline(input: str, output: str, geometry: str,
                 points: int = 4000, seed: int = 42,
                 export_svg: bool = True, cascade_stages: int = 3,
                 enable_plugin_exec: bool = False, pipeline: str | None = None,
                 quiet: bool = True):
    from pathlib import Path
    import sys, os
    from time import time as _time

    # Match CLI path setup
    root = Path(__file__).resolve().parent
    root_src = root / "src"
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root_src))
    os.environ["PYTHONPATH"] = os.pathsep.join([str(root), str(root_src), os.environ.get("PYTHONPATH","")]).strip(os.pathsep)

    inp = Path(input)
    out_base = Path(output)
    expected_svg = out_base.with_suffix(".svg")

    info = {
        "ts": None,
        "input": str(inp),
        "output": str(out_base),
        "geometry": geometry,
        "points": int(points),
        "seed": int(seed),
        "rc": 0,
        "outputs": {
            "expected_svg": str(expected_svg),
            "svg_exists": False,
            "svg_path": None,
            "svg_size": 0,
            "svg_sha256": "",
            "svg_shapes": 0,
        },
        "plugin_exc": "",
        "forced_write": False,
        "forced_write_reason": "",
    }

    t0 = _time()
    # 1) Load geometry
    try:
        geom_mod = load_geometry(geometry)
    except Exception as e:
        info["rc"] = 1
        info["plugin_exc"] = f"ImportError: {e}"
        info["elapsed_s"] = round(_time() - t0, 3)
        return info

    # 2) Ensure output dir
    try:
        ensure_dir(expected_svg)
    except Exception as e:
        info["rc"] = 1
        info["plugin_exc"] = f"DirError: {e}"
        info["elapsed_s"] = round(_time() - t0, 3)
        return info

    # 3) Render + export
    try:
        import traceback as _tb
        doc = None
        if hasattr(geom_mod, "render"):
            doc = geom_mod.render(str(inp), points=int(points), seed=int(seed),
                                  cascade_stages=int(cascade_stages))
        if export_svg:
            if hasattr(geom_mod, "export_svg"):
                geom_mod.export_svg(doc, str(expected_svg))
            elif hasattr(geom_mod, "save_svg"):
                geom_mod.save_svg(doc, str(expected_svg))
            else:
                if doc is not None and hasattr(doc, "write_svg"):
                    doc.write_svg(str(expected_svg))
                else:
                    raise RuntimeError("No exporter found in geometry module")
    except Exception:
        info["rc"] = 1
        import traceback as _tb
        info["plugin_exc"] = _tb.format_exc()

    # 4) Verify file
    if expected_svg.exists():
        size = expected_svg.stat().st_size
        info["outputs"]["svg_exists"] = True
        info["outputs"]["svg_path"] = str(expected_svg)
        info["outputs"]["svg_size"] = size
        info["outputs"]["svg_sha256"] = sha256_file(expected_svg)
        try:
            from tools.svg_audit import count_shapes
            info["outputs"]["svg_shapes"] = int(count_shapes(expected_svg))
        except Exception:
            info["outputs"]["svg_shapes"] = 0
    else:
        folder = expected_svg.parent
        prefix = expected_svg.stem
        cand = sorted(p for p in folder.glob("*.svg") if p.stem.startswith(prefix))
        if cand:
            p = cand[0]
            size = p.stat().st_size
            info["outputs"]["svg_exists"] = True
            info["outputs"]["svg_path"] = str(p)
            info["outputs"]["svg_size"] = size
            info["outputs"]["svg_sha256"] = sha256_file(p)
        else:
            info["rc"] = info["rc"] or 2  # no output

    info["elapsed_s"] = round(_time() - t0, 3)
    return info
"@

# insert before the __main__ guard if present; else append
$guard = '(?ms)^\s*if\s+__name__\s*==\s*["'']__main__["'']\s*:\s*main\(\)\s*$'
if ($text -match $guard) {
  $text = $text -replace $guard, ($fn + "`r`n`r`n" + '$0')
} else {
  $text = $text.TrimEnd() + "`r`n`r`n" + $fn + "`r`n"
}
Set-Content -Encoding utf8NoBOM $File $text
Write-Host "Added run_pipeline() to $File"
