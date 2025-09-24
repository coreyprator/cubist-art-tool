#!/usr/bin/env python3
from __future__ import annotations
import re
import sys
from pathlib import Path
from typing import Tuple

HB = "# === CUBIST STAMP BEGIN ==="
HE = "# === CUBIST STAMP END ==="
FB = "# === CUBIST FOOTER BEGIN ==="
FE = "# === CUBIST FOOTER END ==="


def _split_top(text: str) -> Tuple[str, str]:
    i = 0
    lines = text.splitlines(keepends=True)
    n = len(lines)
    while i < n and (lines[i].startswith("#!") or "coding:" in lines[i][:100]):
        i += 1
    if i < n and lines[i].lstrip().startswith(('"""', "'''")):
        q = '"""' if lines[i].lstrip().startswith('"""') else "'''"
        i += 1
        while i < n and q not in lines[i]:
            i += 1
        if i < n:
            i += 1
    fut = re.compile(r"^\s*from\s+__future__\s+import\s+", re.ASCII)
    while i < n and fut.match(lines[i]):
        i += 1
    return "".join(lines[:i]), "".join(lines[i:])


def _header(path: Path) -> str:
    return "\n".join(
        [
            HB,
            "# Project : Cubist Art",
            f"# File    : {path.as_posix()}",
            "# Version : (stamped by add_headers.py)",
            "# Usage   : (see file)",
            HE,
            "",
        ]
    )


def _footer(path: Path, lines: int) -> str:
    return "\n".join(
        ["", FB, f"# File : {path.as_posix()}", f"# Lines: {lines}", FE, ""]
    )


def _replace(text: str, begin: str, end: str, block: str, top: bool) -> str:
    pat = re.compile(rf"{re.escape(begin)}[\s\S]*?{re.escape(end)}", re.M)
    if re.search(pat, text):
        return re.sub(pat, block, text, count=1)
    return block + text if top else text.rstrip() + "\n" + block


def process_file(path: Path):
    raw = path.read_text(encoding="utf-8")
    pre, rest = _split_top(raw)
    stage = pre + _replace(rest, HB, HE, _header(path), True)
    tmp = _replace(stage, FB, FE, _footer(path, 0), False)
    path.write_text(tmp, encoding="utf-8")
    count = path.read_text(encoding="utf-8").count("\n") + 1
    final = _replace(tmp, FB, FE, _footer(path, count), False)
    changed = final != raw
    path.write_text(final, encoding="utf-8")
    return changed, count


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: python tools/add_headers.py <files...>")
        return 2
    for name in argv:
        p = Path(name)
        if not p.exists():
            print(f"[add_headers] skip (missing): {p.as_posix()}")
            continue
        ch, cnt = process_file(p)
        print(
            f"[add_headers] {'updated' if ch else 'ok'}: {p.as_posix()}  (lines={cnt})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
