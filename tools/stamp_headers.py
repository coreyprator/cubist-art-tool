import argparse
import pathlib
import time
import re
from typing import List, Optional

HEADER_TMPL = (
    "# ======================================================================\n"
    "# File: {fname}\n"
    "# Stamp: {stamp}\n"
    "# (Auto-added header for paste verification)\n"
    "# ======================================================================\n"
)
FOOTER_TMPL = (
    "# ======================================================================\n"
    "# End of File: {fname}  ({stamp})\n"
    "# ======================================================================\n"
)

HEADER_RE = re.compile(
    r"^(?P<pre>(?:#![^\n]*\n)?(?:#.*coding[:=][^\n]*\n)?)"
    r"(?P<header># ======================================================================\n"
    r"# File: .*\n"
    r"# Stamp: .*\n"
    r"# \(Auto-added header for paste verification\)\n"
    r"# ======================================================================\n)",
    re.MULTILINE,
)
FOOTER_RE = re.compile(
    r"(?P<footer># ======================================================================\n"
    r"# End of File: .*\n"
    r"# ======================================================================\n)$",
    re.MULTILINE,
)


def iso_stamp(stamp_arg: str) -> str:
    if stamp_arg == "now":
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return stamp_arg


def parse_globs(csv: Optional[str]) -> List[str]:
    if not csv:
        return []
    return [g.strip() for g in csv.split(",") if g.strip()]


def match_files(
    root: pathlib.Path, includes: List[str], excludes: List[str]
) -> List[pathlib.Path]:
    all_files = set()
    for pattern in includes:
        all_files.update(root.glob(pattern))
    # Exclude
    exclude_files = set()
    for pattern in excludes:
        exclude_files.update(root.glob(pattern))
    return sorted([f for f in all_files if f.is_file() and f not in exclude_files])


def update_header_footer(text: str, fname: str, stamp: str) -> str:
    # Remove old header if present, but preserve shebang/encoding
    m = HEADER_RE.match(text)
    if m:
        pre = m.group("pre")
        text = text[m.end() :]
    else:
        # Check for shebang/encoding at top
        pre = ""
        shebang = ""
        encoding = ""
        lines = text.splitlines(keepends=True)
        idx = 0
        if lines and lines[0].startswith("#!"):
            shebang = lines[0]
            idx += 1
        if idx < len(lines) and "coding" in lines[idx]:
            encoding = lines[idx]
            idx += 1
        pre = shebang + encoding
        text = "".join(lines[idx:])
    # Remove old footer if present
    text = FOOTER_RE.sub("", text).rstrip("\n") + "\n"
    # Add new header/footer
    header = HEADER_TMPL.format(fname=fname, stamp=stamp)
    footer = FOOTER_TMPL.format(fname=fname, stamp=stamp)
    return f"{pre}{header}{text.rstrip()}\n{footer}"


def main():
    parser = argparse.ArgumentParser(
        description="Stamp headers/footers in Python files for paste verification."
    )
    parser.add_argument(
        "--root", type=str, required=True, help="Root directory to search"
    )
    parser.add_argument(
        "--include", type=str, default="**/*.py", help="CSV of glob patterns to include"
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default=".venv/**,.git/**",
        help="CSV of glob patterns to exclude",
    )
    parser.add_argument(
        "--set-stamp", type=str, default="now", help="ISO8601 Zulu stamp or 'now'"
    )
    parser.add_argument("--force", action="store_true", help="Write even if unchanged")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    includes = parse_globs(args.include)
    excludes = parse_globs(args.exclude)
    stamp = iso_stamp(args.set_stamp)

    files = match_files(root, includes, excludes)
    changed = 0
    for f in files:
        orig = f.read_text(encoding="utf-8")
        new = update_header_footer(orig, f.name, stamp)
        if args.force or orig != new:
            f.write_text(new, encoding="utf-8")
            print(f"Stamped: {f}")
            changed += 1
    print(f"Stamped {changed} file(s).")


if __name__ == "__main__":
    main()
