# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: preflight.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:23:58+02:00
# === CUBIST STAMP END ===

# preflight.py
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent

# --------- import heuristics ----------
NAME_TO_IMPORT = {
    "os": "import os",
    "sys": "import sys",
    "json": "import json",
    "argparse": "import argparse",
    "traceback": "import traceback",
    "logging": "import logging",
    "re": "import re",
}

FSTRING_NOPLACEHOLDER_RE = re.compile(r'(^|\s)f("([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\')')

BASENAME_BEGIN = "BEGIN METRICS BASENAME NORMALIZE"
BASENAME_END = "END METRICS BASENAME NORMALIZE"


# --------- IO helpers ----------
def read_text_stripping_bom(p: Path) -> Tuple[str, bool]:
    raw = p.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    if had_bom:
        raw = raw.lstrip(b"\xef\xbb\xbf")
    return raw.decode("utf-8", errors="replace"), had_bom


def write_text_unix(p: Path, s: str) -> None:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    p.write_text(s, encoding="utf-8", newline="\n")


# --------- AST helpers ----------
def ast_imported_names(tree: ast.AST) -> set[str]:
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for alias in n.names:
                out.add((alias.name or "").split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module.split(".")[0])
    return out


def ast_used_names(tree: ast.AST) -> set[str]:
    return {
        n.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    }


# --------- text transforms ----------
def ensure_missing_imports(text: str) -> Tuple[str, List[str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text, []
    imported = ast_imported_names(tree)
    used = ast_used_names(tree)
    need = [
        stmt
        for name, stmt in NAME_TO_IMPORT.items()
        if name in used and name not in imported
    ]
    if not need:
        return text, []
    lines = text.splitlines(True)
    i = 0
    while i < len(lines) and (
        lines[i].startswith("#!")
        or lines[i].lstrip().startswith("#")
        or lines[i].strip() == ""
    ):
        i += 1
    while i < len(lines) and lines[i].lstrip().startswith(("import ", "from ")):
        i += 1
    return "".join(lines[:i] + [n + "\n" for n in need] + lines[i:]), need


def fix_double_with_open(text: str) -> Tuple[str, bool]:
    pat = re.compile(
        r'(?m)^(?P<i>\s*)with\s+open\(\s*args\.metrics_json\s*,\s*"w"\s*,\s*encoding="utf-8"\s*\)\s+as\s+f:\s*\n(?P=i)with\s+open\(\s*args\.metrics_json\s*,\s*"w"\s*,\s*encoding="utf-8"\s*\)\s+as\s+f:\s*\n'
    )
    new, n = pat.subn(
        r'\g<i>with open(args.metrics_json, "w", encoding="utf-8") as f:\n', text
    )
    return new, n > 0


def fix_basename_normalize_newline(text: str) -> Tuple[str, bool]:
    pat = re.compile(
        rf"(?s)(#\s*{re.escape(BASENAME_BEGIN)}.*?)(pass)(\s*#\s*{re.escape(BASENAME_END)})"
    )
    new, n = pat.subn(r"\1pass\n\3", text)
    return new, n > 0


def remove_duplicate_metric_assigns_and_place_globals(text: str) -> Tuple[str, bool]:
    try:
        main_pat = re.compile(
            r"(?s)^\s*def\s+main\s*\([^)]*\)\s*:\s*(.*?)^\s*def\s|\Z", re.M
        )
        m = main_pat.search(text)
        if not m:
            return text, False
        body = m.group(1)
        changed = False

        args_pat = re.compile(r"(?m)^(?P<i>\s*)args\s*=\s*parser\.parse_args\(\)\s*$")
        am = args_pat.search(body)
        if am:
            indent = am.group("i")
            start = am.end()
            tail = body[start:]

            strip_pat = re.compile(
                r"(?m)^\s*global\s+_LAST_METRICS_PATH\s*,\s*_METRICS_STAGES_EXPECTED\s*\n"
                r"|^\s*_LAST_METRICS_PATH\s*=\s*getattr\(args,\s*'metrics_json'.*\)\s*\n"
                r"|^\s*_METRICS_STAGES_EXPECTED\s*=\s*getattr\(args,\s*'cascade_stages'.*\)\s*\n"
            )
            tail2 = (
                strip_pat.sub("", "\n".join(tail.splitlines()[:25]))
                + "\n"
                + "\n".join(tail.splitlines()[25:])
            )
            if tail2 != tail:
                changed = True

            injection = (
                f"{indent}global _LAST_METRICS_PATH, _METRICS_STAGES_EXPECTED\n"
                f"{indent}_LAST_METRICS_PATH = getattr(args, 'metrics_json', None)\n"
                f"{indent}_METRICS_STAGES_EXPECTED = getattr(args, 'cascade_stages', None)\n"
            )
            body = body[:start] + "\n" + injection + tail2

        stray = re.sub(r"(?m)^\s*global\s+_METRICS_STAGES_EXPECTED\s*$", "", body)
        if stray != body:
            changed = True
            body = stray

        if changed:
            text = text[: m.start(1)] + body + text[m.end(1) :]
        return text, changed
    except Exception:
        return text, False


def fix_fstrings_without_placeholders(text: str) -> Tuple[str, int]:
    def repl(m: re.Match) -> str:
        s = m.group(2)
        if "{" in s and "}" in s:
            return m.group(0)
        return m.group(1) + s

    new, n = FSTRING_NOPLACEHOLDER_RE.subn(repl, text)
    return new, n


def strip_trailing_ws(text: str) -> Tuple[str, bool]:
    lines = text.splitlines(True)
    new_lines = [re.sub(r"[ \t]+(\r?\n)$", r"\1", ln) for ln in lines]
    new = "".join(new_lines)
    return new, new != text


# --------- metrics contract injection ----------
ENFORCER_DEF = r"""
def _enforce_metrics_contract(metrics: dict, points: int | None, stages_expected: int | None) -> dict:
    try:
        if not isinstance(metrics, dict):
            return metrics
        t = metrics.setdefault("totals", {})
        if isinstance(points, int):
            t["points"] = int(points)
        if isinstance(stages_expected, int):
            t["stages"] = int(stages_expected)
        # stages as list
        stages = metrics.setdefault("stages", [])
        if not isinstance(stages, list):
            stages = []
            metrics["stages"] = stages
        # pad to stages_expected
        if isinstance(stages_expected, int):
            while len(stages) < stages_expected:
                stages.append(dict(stages[-1]) if stages else {"stage": len(stages)+1})
            if len(stages) > stages_expected:
                del stages[stages_expected:]
        # normalize non-decreasing and cap to points
        prev = 0
        cap = points if isinstance(points, int) else None
        for idx, s in enumerate(stages, start=1):
            if not isinstance(s, dict):
                s = {}
                stages[idx-1] = s
            s.setdefault("stage", idx)
            p = s.get("points", prev)
            if isinstance(p, int):
                p = max(prev, p)
                if isinstance(cap, int):
                    p = min(cap, p)
                s["points"] = p
                prev = p
        # force last to equal points if known
        if isinstance(points, int) and stages:
            stages[-1]["points"] = points
        return metrics
    except Exception:
        return metrics
""".lstrip("\n")


def inject_enforcer_and_rewrite_dump(text: str) -> Tuple[str, bool]:
    changed = False
    if "_enforce_metrics_contract(" not in text:
        # insert after top import block
        text2 = re.sub(
            r"(?s)^((?:(?:from\s+\S+\s+import\s+.+|import\s+\S+).*?\n)+)",
            lambda m: m.group(1) + "\n" + ENFORCER_DEF + "\n",
            text,
            count=1,
        )
        if text2 != text:
            text = text2
            changed = True

    # rewrite `json.dump(_enforce_metrics_contract(metrics_dict, getattr(args, 'points', None), getattr(args, 'cascade_stages', None)), f, ...)` once (captures name of metrics var)
    pat = re.compile(
        r"json\.dump\(\s*(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*,\s*f(?P<trail>[^)]*)\)"
    )

    def repl(m: re.Match) -> str:
        var = m.group("var")
        trail = m.group("trail")
        return (
            f"json.dump(_enforce_metrics_contract({var}, "
            "getattr(args, 'points', None), getattr(args, 'cascade_stages', None)), "
            f"f{trail})"
        )

    text2, n = pat.subn(repl, text, count=1)
    if n:
        changed = True
        text = text2
    return text, changed


# --------- per-file pipeline ----------
def process_file(p: Path, fix: bool) -> List[str]:
    issues: List[str] = []
    text, had_bom = read_text_stripping_bom(p)
    if had_bom:
        issues.append("Removed BOM (U+FEFF) at start of file")

    # import fixes
    t2, added = ensure_missing_imports(text)
    if added:
        issues.append(f"Inserted imports: {', '.join(added)}")
        text = t2

    t2, did = fix_double_with_open(text)
    if did:
        issues.append("Collapsed duplicate with-open block for metrics_json")
        text = t2

    t2, did = fix_basename_normalize_newline(text)
    if did:
        issues.append("Fixed missing newline before END BASENAME NORMALIZE")
        text = t2

    t2, did = remove_duplicate_metric_assigns_and_place_globals(text)
    if did:
        issues.append("Normalized metrics globals & assignments in main()")
        text = t2

    # enforce metrics contract in files that likely write metrics
    if "metrics_json" in text and "json.dump" in text:
        t2, did = inject_enforcer_and_rewrite_dump(text)
        if did:
            issues.append("Wrapped metrics dump with _enforce_metrics_contract")
            text = t2

    t2, nfix = fix_fstrings_without_placeholders(text)
    if nfix:
        issues.append(f"Converted {nfix} f-strings with no placeholders")
        text = t2

    t2, did = strip_trailing_ws(text)
    if did:
        issues.append("Stripped trailing whitespace")
        text = t2

    if fix and issues:
        write_text_unix(p, text)

    return issues


# --------- determinism smoke ----------
def run_determinism_smoke() -> Tuple[bool, str]:
    test = ROOT / "tests" / "test_cascade_metrics_smoke.py"
    cmd = [sys.executable, "-m", "pytest", "-q", str(test if test.exists() else ROOT)]
    cp = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    return (cp.returncode == 0), cp.stdout


# --------- main ----------
def main():
    ap = argparse.ArgumentParser(
        description="Preflight: scan & auto-fix common repo issues."
    )
    ap.add_argument("--fix", action="store_true", help="Apply safe fixes in-place")
    ap.add_argument(
        "--det", action="store_true", help="Run determinism smoke test after fixes"
    )
    args = ap.parse_args()

    files: List[Path] = []
    for path, dirs, fnames in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".venv", ".git", "__pycache__"}]
        for name in fnames:
            if name.endswith(".py"):
                files.append(Path(path) / name)

    actionable = 0
    for p in sorted(files):
        rel = p.relative_to(ROOT)
        issues = process_file(p, fix=args.fix)
        if issues:
            actionable += 1
            print(f"[{rel}]")
            for msg in issues:
                print(f"  - {msg}")

    if actionable == 0:
        print("✅ Preflight: no actionable issues found.")
    else:
        print(f"Preflight finished with {actionable} actionable issue(s).")

    if args.det:
        ok, out = run_determinism_smoke()
        if ok:
            print(
                "\nDeterminism check PASSED: sanitized metrics are identical across runs."
            )
        else:
            print("\nCLI returned non-zero during determinism test. Logs:")
            print("  " + "\n  ".join(out.splitlines()))


if __name__ == "__main__":
    main()


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:23:58+02:00
# === CUBIST FOOTER STAMP END ===
