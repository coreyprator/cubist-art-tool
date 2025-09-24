from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict


BUF = 1024 * 1024


def sha256_file(path: Path) -> str:
    path = Path(path)
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(BUF)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def file_size(path: Path) -> int:
    path = Path(path)
    try:
        return path.stat().st_size
    except Exception:
        return 0


def head_tail_bytes(path: Path, head: int = 256, tail: int = 256) -> Dict[str, str]:
    path = Path(path)
    if not path.exists():
        return {"head": "", "tail": ""}
    bs = path.read_bytes()
    hb = bs[:head]
    tb = bs[-tail:]

    # represent as safe ascii with escapes
    def to_text(b: bytes) -> str:
        try:
            return b.decode("utf-8", errors="replace")
        except Exception:
            return str(list(b))

    return {"head": to_text(hb), "tail": to_text(tb)}
