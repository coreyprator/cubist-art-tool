"""
Stable import surface for Cubism v2.3.7.x.
Downstream code and tests should import from here.
"""

from __future__ import annotations

from pathlib import Path


def _normalize_kwargs(args, kwargs):
    # If positional provided, treat as (input, output, geometry)
    if args:
        a = list(args)
        if len(a) >= 1:
            kwargs.setdefault("input", a[0])
        if len(a) >= 2:
            kwargs.setdefault("output", a[1])
        if len(a) >= 3:
            kwargs.setdefault("geometry", a[2])

    # Common synonyms -> canonical
    mapping = {
        # input
        "input_path": "input",
        "in_path": "input",
        "src": "input",
        "image": "input",
        # output
        "output_path": "output",
        "out_path": "output",
        "output_stem": "output",
        "out": "output",
        # geometry / mode
        "mode": "geometry",
        "plugin": "geometry",
        "shape": "geometry",
        "algorithm": "geometry",
        "algo": "geometry",
        "kind": "geometry",
        "geom": "geometry",
        "geometry_name": "geometry",
        "pattern": "geometry",
        # tuning
        "n_points": "points",
        "num_points": "points",
        "random_seed": "seed",
        "stages": "cascade_stages",
        "plugin_exec": "enable_plugin_exec",
        "enable_exec": "enable_plugin_exec",
    }
    for k, v in list(kwargs.items()):
        if k in mapping:
            kwargs.setdefault(mapping[k], v)
            kwargs.pop(k, None)

    # Compose output from dir+stem if provided
    out_dir = (
        kwargs.pop("output_dir", None)
        or kwargs.pop("out_dir", None)
        or kwargs.pop("dir", None)
        or kwargs.pop("folder", None)
    )
    out_stem = kwargs.get("output") or kwargs.get("output_stem") or kwargs.get("out")
    if out_dir and out_stem and not kwargs.get("output"):
        kwargs["output"] = str(Path(out_dir) / Path(out_stem).name)

    # Default output from input if still missing
    if "output" not in kwargs and "input" in kwargs:
        p = Path(str(kwargs["input"]))
        kwargs["output"] = str(p.with_suffix(""))

    # Default geometry if still missing (harmless default; tests iterate explicit modes anyway)
    if "geometry" not in kwargs:
        kwargs["geometry"] = "delaunay"

    # Casts
    for k in ("points", "seed", "cascade_stages"):
        if k in kwargs and kwargs[k] is not None:
            try:
                kwargs[k] = int(kwargs[k])
            except Exception:
                pass

    # Only pass keys the CLI pipeline knows about
    allowed = {
        "input",
        "output",
        "geometry",
        "points",
        "seed",
        "export_svg",
        "cascade_stages",
        "enable_plugin_exec",
        "pipeline",
        "quiet",
    }
    return {k: v for k, v in kwargs.items() if k in allowed}


def run_cubist(*args, **kwargs):
    kw = _normalize_kwargs(args, dict(kwargs))

    # Try modern in-core pipeline first (resolved at call time).
    try:
        from cubist_core_logic import run_pipeline as _run_pipeline  # type: ignore[attr-defined]
    except Exception:
        _run_pipeline = None
    if _run_pipeline is not None:
        return _run_pipeline(**kw)

    # Fallback to CLI programmatic pipeline.
    try:
        from cubist_cli import run_pipeline as _cli_run
    except Exception as e:
        raise ImportError(
            "run_cubist fallback failed: cubist_cli.run_pipeline not available"
        ) from e
    return _cli_run(**kw)
