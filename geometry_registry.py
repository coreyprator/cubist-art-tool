# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: geometry_registry.py
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:29+02:00
# === CUBIST STAMP END ===

# ============================================================================
# Cubist Art Tool — Geometry Plugin Registry
# File: geometry_registry.py
# Version: v2.3-fix1
# Date: 2025-09-01
# Summary:
#   Discovers geometry plugins from a directory (e.g., geometry_plugins/).
#   Plugins may register via:
#     1) def register(register_geometry): ...
#     2) GEOMETRY_MODES = {"name": callable, ...}
#     3) A callable named like the module stem (e.g. concentric_circles()).
#   Exposes:
#     - register(name, fn), get_geometry(name)
#     - names() -> list of registered names
#     - _registry (alias for tests) -> internal dict of callables
# ============================================================================

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Callable, Dict, Optional, Iterable

# Canonical internal registry and test-compat alias.
_REGISTRY: Dict[str, Callable[..., object]] = {}
_registry = _REGISTRY  # tests assert this exists


def register(name: str, fn: Callable[..., object]) -> None:
    """Register a geometry generator callable under a case-insensitive name."""
    key = (name or "").strip().lower()
    if not key:
        raise ValueError("Plugin name must be a non-empty string.")
    _REGISTRY[key] = fn


def register_geometry(name: str, fn: Callable[..., object]) -> None:
    """Alias passed to plugins' register(entrypoint) hook."""
    register(name, fn)


def get_geometry(name: str) -> Optional[Callable[..., object]]:
    """Return a registered geometry callable by name, or None."""
    return _REGISTRY.get((name or "").strip().lower())


def names() -> Iterable[str]:
    """Return sorted registered geometry names."""
    return sorted(_REGISTRY.keys())


def _try_register_stem_callable(module, stem: str) -> None:
    """If the module defines a callable with the same name as its stem, register it."""
    try:
        cand = getattr(module, stem, None)
        if callable(cand):
            register(stem, cand)
    except Exception:
        pass


def load_plugins(directory: str | Path) -> None:
    """
    Import all *.py files in the directory as modules. Each module should either:
      - define `def register(register_geometry): ...` and call it; or
      - export `GEOMETRY_MODES = {"name": callable, ...}`; or
      - define a callable named like the module stem (fallback).
    Import/registration errors for individual plugins are isolated.
    """
    dir_path = Path(directory).resolve()
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"[plugins] load complete: dir={dir_path} names=", flush=True)
        return

    discovered: list[str] = []
    for path in sorted(dir_path.glob("*.py")):
        stem = path.stem
        mod_name = f"geomplug_{stem}"
        try:
            spec = importlib.util.spec_from_file_location(mod_name, str(path))
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)  # type: ignore[attr-defined]

            # Mode 1: register(entrypoint)
            if hasattr(module, "register") and callable(module.register):  # type: ignore[attr-defined]
                try:
                    module.register(register_geometry)  # type: ignore[attr-defined]
                except Exception:
                    pass

            # Mode 2: GEOMETRY_MODES mapping
            modes = getattr(module, "GEOMETRY_MODES", None)
            if isinstance(modes, dict):
                for k, v in modes.items():
                    if callable(v):
                        try:
                            register(k, v)
                        except Exception:
                            pass

            # Mode 3: stem-named callable
            _try_register_stem_callable(module, stem)

        except Exception:
            # Ignore this plugin file, continue with others
            continue

    discovered = list(names())
    # Print summary similar to your previous captured stdout
    summary = ", ".join(discovered)
    print(f"[plugins] load complete: dir={dir_path} names={summary}", flush=True)


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:29+02:00
# === CUBIST FOOTER STAMP END ===
