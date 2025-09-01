#!/usr/bin/env python3
# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tools/collect_dirty_diagnostics.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:24:02+02:00
# === CUBIST STAMP END ===
# =============================================================================
# Cubist Art — Dirty Tree Diagnostics (read-only)
# File: tools/collect_dirty_diagnostics.py
# Version: 1.0.0
# Build: 2025-09-01T10:45:00
# =============================================================================
# What this script does (read-only):
#   - Verifies you're in a Git repo
#   - Collects detailed diagnostics about the working tree:
#       * system & tool versions (Python, Git)
#       * repo root, current branch, remotes, safe.directory
#       * git status (human + porcelain)
#       * lists of changed, untracked, ignored files
#       * CRLF / line-ending related git config
#       * top file extensions among changed files
#       * optional diffs (with a size cap)
#       * contents of .gitignore, .gitattributes, .pre-commit-config.yaml if present
#   - Writes everything to logs/diagnostics/<timestamp>/git-dirty-diagnostic.txt
#   - Optionally zips the report folder for easy sharing
# =============================================================================

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple
import zipfile


def now_stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def stamp_for_path() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def run(cmd: List[str]) -> Tuple[int, str]:
    """Run a command, return (exit_code, combined_output)."""
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=False,
        )
        return res.returncode, res.stdout or ""
    except Exception as e:
        return 127, f"[exec-error] {e}"


class Logger:
    def __init__(self, logfile: Path):
        self.logfile = logfile
        logfile.parent.mkdir(parents=True, exist_ok=True)

    def write(self, s: str = "") -> None:
        s = s.rstrip("\n")
        # Mirror to console
        print(s)
        # Append to file
        with self.logfile.open("a", encoding="utf-8", newline="\n") as f:
            f.write(s + "\n")

    def section(self, title: str) -> None:
        line = "=" * 80
        self.write("")
        self.write(line)
        self.write(f"== {title}")
        self.write(line)

    def headerblock(self, lines: List[str]) -> None:
        for ln in lines:
            self.write(ln)


def assert_git_repo(log: Logger) -> Path:
    code, out = run(["git", "rev-parse", "--show-toplevel"])
    if code != 0 or not out.strip():
        log.write("[error] This directory is not a Git repository.")
        sys.exit(2)
    repo_root = Path(out.strip())
    return repo_root


def show_cmd(log: Logger, label: str, cmd: List[str], ignore_exit: bool = True) -> None:
    log.section(f"RUN {label}")
    log.write("> " + " ".join(cmd))
    code, out = run(cmd)
    if out:
        log.write(out.rstrip("\n"))
    log.write(f"[exit] {code}")
    if not ignore_exit and code != 0:
        log.write(f"[error] Command failed ({code}): {' '.join(cmd)}")
        sys.exit(code)


def print_if_exists(log: Logger, path: Path, label: str) -> None:
    log.section(f"File: {label}")
    if path.exists():
        log.write(f"[exists] {path}")
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            log.write(content)
        except Exception as e:
            log.write(f"[read-error] {e}")
    else:
        log.write(f"[missing] {path}")


def changed_extensions_from_porcelain(porcelain: str) -> List[Tuple[str, int]]:
    counts = {}
    for line in porcelain.splitlines():
        if not line.strip():
            continue
        # format: "XY<space>path"
        if len(line) >= 4:
            path = line[3:]
        else:
            continue
        ext = Path(path).suffix.lower() or "(noext)"
        counts[ext] = counts.get(ext, 0) + 1
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)


def append_trimmed_diffs(
    log: Logger, header: str, content: str, remaining_bytes: int, which: str
) -> int:
    log.section(header)
    data = content.encode("utf-8", errors="replace")
    if len(data) <= remaining_bytes:
        log.write(content)
        return remaining_bytes - len(data)
    # Trim safely at byte boundary
    trimmed = data[: max(0, remaining_bytes)].decode("utf-8", errors="ignore")
    log.write(trimmed)
    omitted = len(data) - max(0, remaining_bytes)
    log.write(f"[truncated {which}] {omitted} bytes omitted")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="collect_dirty_diagnostics.py",
        description="Collect read-only Git working-tree diagnostics with optional diffs.",
    )
    ap.add_argument(
        "--include-diffs",
        action="store_true",
        help="Include unstaged and staged diffs (truncated to --max-diff-bytes).",
    )
    ap.add_argument(
        "--max-diff-bytes",
        type=int,
        default=120_000,
        help="Max total bytes of diffs to include (default: 120000).",
    )
    ap.add_argument(
        "--zip",
        action="store_true",
        help="Zip the diagnostics folder for easy sharing.",
    )
    args = ap.parse_args()

    # Prepare logging
    # Try to anchor under the repo root (if possible).
    tmp_repo_check_code, tmp_repo_out = run(["git", "rev-parse", "--show-toplevel"])
    if tmp_repo_check_code == 0 and tmp_repo_out.strip():
        repo_root = Path(tmp_repo_out.strip())
    else:
        repo_root = Path.cwd()

    out_dir = repo_root / "logs" / "diagnostics" / stamp_for_path()
    out_dir.mkdir(parents=True, exist_ok=True)
    log_file = out_dir / "git-dirty-diagnostic.txt"
    log = Logger(log_file)

    # Header
    log.write("Cubist Art — Dirty Tree Diagnostics")
    log.write(f"When: {now_stamp()}")
    log.write(f"Report folder: {out_dir}")

    # Verify repo and switch CWD to repo root for consistency
    repo_root = assert_git_repo(log)
    os.chdir(repo_root)
    log.write(f"Repo root: {repo_root}")

    # System & tool versions
    log.section("System & Tool Versions")
    log.write(f"Python: {sys.executable}")
    log.write(sys.version.replace("\n", " ").strip())
    log.write(f"Platform: {platform.platform()}")
    show_cmd(log, "git --version", ["git", "--version"])

    # Repo basics
    log.section("Repo Basics")
    show_cmd(
        log, "git rev-parse --show-toplevel", ["git", "rev-parse", "--show-toplevel"]
    )
    show_cmd(log, "git branch --show-current", ["git", "branch", "--show-current"])
    show_cmd(log, "git remote -v", ["git", "remote", "-v"])
    show_cmd(
        log,
        "git config --global --get-all safe.directory",
        ["git", "config", "--global", "--get-all", "safe.directory"],
    )

    # VERSION (if present)
    print_if_exists(log, repo_root / "VERSION", "VERSION")

    # Status summaries
    log.section("Git Status (human)")
    show_cmd(log, "git status", ["git", "status"])

    log.section("Git Status (porcelain v1, untracked)")
    code_por, out_por = run(["git", "status", "--porcelain=v1", "-uall"])
    log.write("> git status --porcelain=v1 -uall")
    log.write(out_por.rstrip("\n"))
    log.write(f"[exit] {code_por}")

    log.section("Name-only diffs vs HEAD (tracked)")
    show_cmd(
        log, "git diff --name-status HEAD", ["git", "diff", "--name-status", "HEAD"]
    )
    show_cmd(log, "git diff --name-only HEAD", ["git", "diff", "--name-only", "HEAD"])

    log.section("Untracked files (not ignored)")
    show_cmd(
        log,
        "git ls-files --others --exclude-standard",
        ["git", "ls-files", "--others", "--exclude-standard"],
    )

    log.section("Ignored files snapshot")
    show_cmd(log, "git status --ignored", ["git", "status", "--ignored"])

    # Line-ending / CRLF config
    log.section("Line-ending / CRLF Config")
    show_cmd(
        log, "git config --show-origin -l", ["git", "config", "--show-origin", "-l"]
    )

    # Key dotfiles
    print_if_exists(log, repo_root / ".gitignore", ".gitignore")
    print_if_exists(log, repo_root / ".gitattributes", ".gitattributes")
    print_if_exists(
        log, repo_root / ".pre-commit-config.yaml", ".pre-commit-config.yaml"
    )

    # Changed file extensions summary
    log.section("Changed File Extensions (from porcelain)")
    for ext, count in changed_extensions_from_porcelain(out_por):
        log.write(f"{count:8d}  {ext}")

    # Optional diffs with truncation
    if args.include_diffs:
        remaining = max(0, int(args.max_diff_bytes))
        code_u, out_u = run(["git", "diff"])
        remaining = append_trimmed_diffs(
            log, "Diff (unstaged)", out_u, remaining, "unstaged"
        )
        if remaining > 0:
            code_s, out_s = run(["git", "diff", "--staged"])
            remaining = append_trimmed_diffs(
                log, "Diff (staged)", out_s, remaining, "staged"
            )
        else:
            log.section("Diffs")
            log.write("[diffs] byte budget exhausted before staged diff")
    else:
        log.section("Diffs")
        log.write("[skipped] Use --include-diffs to include diffs in the report.")

    # Footer + optional zip
    log.section("Done")
    log.write(f"Report saved to: {log_file}")

    if args.zip:
        zip_path = out_dir.with_suffix(".zip")
        try:
            if zip_path.exists():
                zip_path.unlink()
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for p in out_dir.rglob("*"):
                    if p.is_file():
                        zf.write(p, arcname=p.relative_to(out_dir.parent))
            log.write(f"Zipped report: {zip_path}")
        except Exception as e:
            log.write(f"[zip-error] {e}")

    # also echo a friendly final line to stdout
    print(f"{now_stamp()} [diagnostics] complete -> {out_dir}")


if __name__ == "__main__":
    main()


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:24:02+02:00
# === CUBIST FOOTER STAMP END ===
