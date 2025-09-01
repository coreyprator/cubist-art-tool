#!/usr/bin/env python3
"""
Stamp headers and footers across the repo.

- Preserves original line endings (\n vs \r\n) per file.
- Inserts after a shebang if present.
- Idempotent: updates existing stamp blocks or adds them if missing.
- Skips common build/cache/output folders.
- **Self-protects**: never stamps this file (tools/stamp_repo.py) or any file
  that defines HEADER_BEGIN/FOOTER_BEGIN as Python variables.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import subprocess
from pathlib import Path
from typing import Iterable

# --- Constants ----------------------------------------------------------------

HEADER_BEGIN = "# === CUBIST STAMP BEGIN ==="
HEADER_END = "# === CUBIST STAMP END ==="

FOOTER_BEGIN = "# === CUBIST FOOTER STAMP BEGIN ==="
FOOTER_END = "# === CUBIST FOOTER STAMP END ==="

# Directories to skip entirely (by name)
SKIP_DIRS = {
    ".git",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "node_modules",
    "__pycache__",
    "output",
    "outputs",
    "logs",
    "build",
    "dist",
    "tmp",
    "tmp_release_smoke",
    "Archived Output",
}

# Individual files to skip (repo-relative POSIX paths)
SKIP_FILES = {
    "tools/stamp_repo.py",  # <- self-protection
    "tools/archived/stamp_headers_legacy.py",
}

# File extensions to stamp
DEFAULT_EXTS = {".py", ".ps1", ".md"}

# Precompiled patterns to find existing blocks
_HEADER_RE = re.compile(
    rf"{re.escape(HEADER_BEGIN)}.*?{re.escape(HEADER_END)}\r?\n?", re.DOTALL
)
_FOOTER_RE = re.compile(
    rf"{re.escape(FOOTER_BEGIN)}.*?{re.escape(FOOTER_END)}\r?\n?", re.DOTALL
)


# --- Helpers ------------------------------------------------------------------


def _now_iso() -> str:
    # Always second precision (stable for diffs)
    return _dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def _get_git_commit(root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=str(root)
        )
        return out.decode("utf-8", "replace").strip()
    except Exception:
        return "n/a"


def _line_ending_for(text: str) -> str:
    # Simple and reliable: if CRLF exists anywhere, keep CRLF, else LF
    return "\r\n" if "\r\n" in text else "\n"


def _relpath(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root).as_posix())
    except Exception:
        return p.name


def _should_skip_dir(dirpath: Path) -> bool:
    return dirpath.name in SKIP_DIRS


def _iter_files(root: Path, exts: set[str]) -> Iterable[Path]:
    for dp, dn, fn in os.walk(root):
        dp_path = Path(dp)
        # prune directories in-place to avoid walking them
        dn[:] = [d for d in dn if not _should_skip_dir(dp_path / d)]
        for name in fn:
            p = dp_path / name
            if p.suffix.lower() in exts:
                yield p


def _build_header(
    relpath: str, version: str, build_ts: str, commit: str, nl: str
) -> str:
    # Separate "header block" from the rest with an extra newline after END.
    parts = [
        HEADER_BEGIN,
        "# Project: Cubist Art",
        f"# File: {relpath}",
        f"# Version: {version}",
        f"# Build: {build_ts}",
        f"# Commit: {commit}",
        f"# Stamped: {_now_iso()}",
        HEADER_END,
        "",  # blank line after header
    ]
    return nl.join(parts)


def _build_footer(version: str, nl: str) -> str:
    parts = [
        "",  # ensure a newline before footer block
        FOOTER_BEGIN,
        f"# End of file - {version} - stamped {_now_iso()}",
        FOOTER_END,
        "",  # final newline at end of file
    ]
    return nl.join(parts)


def _insert_after_shebang(text: str, insert_block: str, nl: str) -> str:
    if text.startswith("#!"):
        first, _, rest = text.partition(nl)
        return first + nl + insert_block + rest
    return insert_block + text


def _should_skip_file_by_content(path: Path, raw: str) -> bool:
    """
    Skip any file that defines HEADER_BEGIN/FOOTER_BEGIN variables (like this script),
    so our marker text inside string literals is never replaced.
    """
    if "HEADER_BEGIN =" in raw or "FOOTER_BEGIN =" in raw:
        return True
    return False


def _stamp_one_file(
    path: Path, root: Path, version: str, build_ts: str, commit: str, dry_run: bool
) -> bool:
    """
    Returns True if file was changed.
    """
    raw = path.read_text(encoding="utf-8", errors="ignore")
    nl = _line_ending_for(raw)
    rel = _relpath(path, root)

    # Self-protection: skip this stamper (or any file on the explicit skip list)
    if rel in SKIP_FILES or _should_skip_file_by_content(path, raw):
        return False

    # Build new header/footer blocks with the file's newline style.
    new_header = _build_header(rel, version, build_ts, commit, nl)
    new_footer = _build_footer(version, nl)

    # Replace or insert header
    if _HEADER_RE.search(raw):
        raw2 = _HEADER_RE.sub(new_header, raw, count=1)
    else:
        raw2 = _insert_after_shebang(raw, new_header, nl)

    # Replace or append footer
    if _FOOTER_RE.search(raw2):
        raw3 = _FOOTER_RE.sub(new_footer, raw2, count=1)
    else:
        # ensure single trailing newline before appending footer
        if not raw2.endswith(nl):
            raw2 = raw2 + nl
        raw3 = raw2 + new_footer

    changed = raw3 != raw
    if changed and not dry_run:
        # Write back exactly what we constructed (content contains the intended NLs)
        path.write_text(raw3, encoding="utf-8", newline="")
    return changed


# --- CLI ---------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description="Stamp repo headers/footers.")
    ap.add_argument("--version", required=True, help="Semantic version like v2.3.7")
    ap.add_argument(
        "--build-ts",
        required=True,
        help="Build timestamp (e.g. 2025-09-01T11:11:06)",
    )
    ap.add_argument(
        "--root", default=".", help="Repository root (default: current directory)"
    )
    ap.add_argument(
        "--ext",
        action="append",
        dest="exts",
        help=f"Extra extension to include (defaults: {', '.join(sorted(DEFAULT_EXTS))})",
    )
    ap.add_argument("--dry-run", action="store_true", help="Report only; no writes")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    exts = set(DEFAULT_EXTS)
    if args.exts:
        exts |= {("." + e.lstrip(".")).lower() for e in args.exts}

    commit = _get_git_commit(root)

    total = 0
    changed = 0
    for f in _iter_files(root, exts):
        total += 1
        if _stamp_one_file(f, root, args.version, args.build_ts, commit, args.dry_run):
            changed += 1

    print("[stamp_repo] stamped={} / {} files under {}".format(changed, total, root))


if __name__ == "__main__":
    main()
