# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tools/stamp_repo.py
# Version: v2.3.6
# Build: 2025-09-01T09:20:00
# Commit: n/a
# Stamped: 2025-09-01T09:20:00
# === CUBIST STAMP END ===
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple

HEADER_BEGIN = "# === CUBIST STAMP BEGIN ==="
HEADER_END = "# === CUBIST STAMP END ==="
FOOTER_BEGIN = "# === CUBIST FOOTER STAMP BEGIN ==="
FOOTER_END = "# === CUBIST FOOTER STAMP END ==="

# Directories to skip entirely
EXCLUDE_DIRS = {
    ".venv",
    "__pycache__",
    ".git",
    "build",
    "dist",
    "output",
    "logs",
    ".idea",
    ".vscode",
    ".pytest_cache",
}

# Additional glob-style directory name fragments to skip if found in a path
EXCLUDE_FRAGMENTS = {"Archived Output"}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _replace_region(
    text: str, begin: str, end: str, replacement: str
) -> Tuple[str, bool]:
    if begin in text and end in text:
        pre, rest = text.split(begin, 1)
        _, post = rest.split(end, 1)
        return pre + replacement + post, True
    return text, False


def _has_shebang(text: str) -> bool:
    return text.startswith("#!")


def _make_header(
    rel_path: str, version: str, build_ts: str, commit: str | None, stamped: str
) -> str:
    lines = [
        HEADER_BEGIN,
        "# Project: Cubist Art",
        f"# File: {rel_path}",
        f"# Version: {version}",
        f"# Build: {build_ts}",
        f"# Commit: {commit or 'n/a'}",
        f"# Stamped: {stamped}",
        HEADER_END,
        "",
    ]
    return "\n".join(lines)


def _make_footer(version: str, stamped: str) -> str:
    lines = [
        "",
        FOOTER_BEGIN,
        f"# End of file - {version} - stamped {stamped}",
        FOOTER_END,
        "",
    ]
    return "\n".join(lines)


def _should_skip(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    if any(ex.lower() in parts for ex in EXCLUDE_DIRS):
        return True
    if any(
        fragment.lower() in ("/".join(path.parts)).lower()
        for fragment in EXCLUDE_FRAGMENTS
    ):
        return True
    return False


def iter_py_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        if _should_skip(p):
            continue
        yield p


def stamp_file(
    path: Path, repo_root: Path, version: str, build_ts: str, commit: str | None
) -> bool:
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    original = path.read_text(encoding="utf-8", errors="ignore")
    stamped_ts = _now()

    header = _make_header(rel, version, build_ts, commit, stamped_ts)
    footer = _make_footer(version, stamped_ts)

    # Replace or insert header
    updated, replaced_header = _replace_region(
        original, HEADER_BEGIN, HEADER_END, header
    )
    if not replaced_header:
        if _has_shebang(updated):
            first_nl = updated.find("\n")
            first_nl = first_nl if first_nl >= 0 else 0
            updated = updated[: first_nl + 1] + header + updated[first_nl + 1 :]
        else:
            updated = header + updated

    # Replace or append footer
    updated2, replaced_footer = _replace_region(
        updated, FOOTER_BEGIN, FOOTER_END, footer
    )
    if replaced_footer:
        updated = updated2
    else:
        if not updated.endswith("\n"):
            updated += "\n"
        updated = updated + footer

    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stamp all Python files with version/date header and footer."
    )
    parser.add_argument("--version", required=True, help="Version string, e.g. v2.3.6")
    parser.add_argument(
        "--build-ts", default=None, help="Build ISO timestamp (default: now)"
    )
    parser.add_argument("--commit", default=None, help="Commit short hash (optional)")
    parser.add_argument(
        "--root", default=".", help="Repo root (default: current directory)"
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    version = args.version
    build_ts = args.build_ts or _now()
    commit = args.commit

    changed = 0
    total = 0
    for fpath in iter_py_files(root):
        total += 1
        if stamp_file(fpath, root, version, build_ts, commit):
            changed += 1
    print(f"[stamp_repo] stamped={changed} / {total} files under {root}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.6 - stamped 2025-09-01T09:20:00
# === CUBIST FOOTER STAMP END ===
