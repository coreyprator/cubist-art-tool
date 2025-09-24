from __future__ import annotations

import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable, Tuple, Any

# Enable with: $env:CUBIST_TRACE = '1' (PowerShell) or export CUBIST_TRACE=1
TRACE: bool = os.environ.get("CUBIST_TRACE", "0") in ("1", "true", "TRUE", "on", "ON")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def t(msg: str) -> None:
    """Lightweight stderr tracer."""
    if TRACE:
        print(f"[trace _trace {_ts()}] {msg}", file=sys.stderr)


# ------------------------------ helpers --------------------------------------


def file_info(p: str | Path) -> dict[str, Any]:
    p = Path(p)
    if not p.exists():
        return {"exists": False, "name": p.name, "parent": str(p.parent)}
    return {
        "exists": True,
        "size": p.stat().st_size,
        "name": p.name,
        "parent": str(p.parent),
    }


def sha256_file(p: str | Path) -> str:
    p = Path(p)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# Stats and dumps --------------------------------------------------------------


def try_stats(
    samples: Iterable[Tuple[float, float, float]]
    | Iterable[Tuple[float, float]]
    | Iterable[Any],
) -> dict:
    xs, ys, rs = [], [], []
    n = 0
    for s in samples or []:
        try:
            x = float(s[0])
            y = float(s[1])
            r = float(s[2]) if len(s) > 2 else None
        except Exception:
            continue
        xs.append(x)
        ys.append(y)
        rs.append(r) if r is not None else None
        n += 1
    out = {"n": n}
    if xs:
        out.update(
            {
                "xmin": min(xs),
                "xmax": max(xs),
                "ymin": min(ys),
                "ymax": max(ys),
            }
        )
    if rs and any(r is not None for r in rs):
        rvals = [r for r in rs if r is not None]
        out.update(
            {
                "r_min": min(rvals),
                "r_max": max(rvals),
                "r_mean": sum(rvals) / len(rvals) if rvals else 0.0,
            }
        )
    return out


def dump(label: str, data: Any) -> None:
    if TRACE:
        try:
            print(
                f"[dump] {json.dumps({'ts': _ts(), 'label': label, 'data': data}, separators=(',', ':'))}",
                file=sys.stderr,
            )
        except Exception:
            # Fallback if data isn't JSON-serializable
            print(
                f"[dump] {{'ts':'{_ts()}','label':'{label}','data':str(data)}}",
                file=sys.stderr,
            )
