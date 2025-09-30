"""
Safer preflight script: only normalize f-strings that contain NO formatted values,
and skip files that are known to generate HTML or declare a PREFLIGHT_SKIP marker.

Rules:
- Files listed in SKIP_FILES are skipped entirely.
- Files that contain the marker "# PREFLIGHT_SKIP" are skipped.
- For other .py files, we scan STRING tokens; if a token is an f-string but its AST
  expression contains no ast.FormattedValue nodes, we remove the 'f'/'F' flag.
This prevents corruption of template strings which *do* include placeholders.
"""
from __future__ import annotations

import ast
import io
import os
import re
import tokenize
from typing import List

# Configure skip list for files that generate HTML or are fragile
SKIP_FILES = {
    "tools/prod_ui.py",
    "tools/make_gallery.py",
    # Add more relative paths if needed
}

PREFLIGHT_SKIP_MARKER = "# PREFLIGHT_SKIP"


def is_path_skipped(path: str) -> bool:
    rel = os.path.relpath(path).replace("\\", "/")
    for p in SKIP_FILES:
        if rel.endswith(p) or os.path.normpath(rel).endswith(os.path.normpath(p)):
            return True
    return False


def file_contains_skip_marker(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for _ in range(40):  # quick scan top lines
                line = fh.readline()
                if not line:
                    break
                if PREFLIGHT_SKIP_MARKER in line:
                    return True
    except Exception:
        return False
    return False


def strip_f_prefix_from_string_token(token_string: str) -> str:
    """
    Given a token string literal (including quotes and prefixes), remove 'f'/'F'
    from its prefix only if the parsed AST shows no FormattedValue nodes.
    """
    # Quick check: does the prefix include f/F?
    m = re.match(r"(?P<prefix>(?:[rubfRUBF])*)(?P<quote>['\"]{1,3})", token_string)
    if not m:
        return token_string
    prefix = m.group("prefix")
    if "f" not in prefix.lower():
        return token_string

    # Attempt to parse the token string as Python expression to inspect AST
    try:
        expr = ast.parse(token_string, mode="eval").body
    except Exception:
        # If parsing fails, be conservative and do not remove f
        return token_string

    # If AST is JoinedStr (f-string), ensure it contains no FormattedValue
    if isinstance(expr, ast.JoinedStr):
        has_formatted = any(isinstance(node, ast.FormattedValue) for node in ast.walk(expr))
        if has_formatted:
            return token_string  # contains placeholders -> do not change
        # Safe to remove 'f'/'F' from prefix: reconstruct token string
        new_prefix = prefix.replace("f", "").replace("F", "")
        # Build new token: new_prefix + rest of token (strip old prefix)
        rest = token_string[len(prefix):]
        return new_prefix + rest

    # Not a JoinedStr -> leave unchanged
    return token_string


def process_file(path: str) -> bool:
    """
    Tokenize file, modify STRING tokens as necessary, and write back if changed.
    Returns True if file was modified.
    """
    if is_path_skipped(path) or file_contains_skip_marker(path):
        print(f"[preflight] skipping (configured): {path}")
        return False

    try:
        with tokenize.open(path) as fh:
            src = fh.read()
    except Exception as e:
        print(f"[preflight] read error {path}: {e}")
        return False

    modified = False
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except Exception as e:
        print(f"[preflight] tokenize error {path}: {e}")
        return False

    new_tokens: List[tokenize.TokenInfo] = []

    for tok in tokens:
        if tok.type == tokenize.STRING:
            original = tok.string
            new_string = strip_f_prefix_from_string_token(original)
            if new_string != original:
                modified = True
                tok = tokenize.TokenInfo(tok.type, new_string, tok.start, tok.end, tok.line)
        new_tokens.append(tok)

    if modified:
        try:
            new_src = tokenize.untokenize(new_tokens)
            # Safety: write to temporary then replace
            tmp_path = path + ".preflight.tmp"
            with open(tmp_path, "w", encoding="utf-8", newline="") as outf:
                outf.write(new_src)
            os.replace(tmp_path, path)
            print(f"[preflight] updated: {path}")
            return True
        except Exception as e:
            print(f"[preflight] write error {path}: {e}")
            # cleanup
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            return False

    return False


def discover_python_files(root: str) -> List[str]:
    pyfiles = []
    for dirpath, dirnames, filenames in os.walk(root):
        # skip venv, .git, node_modules
        if any(part in ("venv", ".venv", ".git", "node_modules") for part in dirpath.split(os.sep)):
            continue
        for fn in filenames:
            if fn.endswith(".py"):
                pyfiles.append(os.path.join(dirpath, fn))
    return pyfiles


def main():
    root = os.getcwd()
    files = discover_python_files(root)
    changed = []
    for f in files:
        try:
            if process_file(f):
                changed.append(f)
        except Exception as e:
            print(f"[preflight] error processing {f}: {e}")
    print(f"[preflight] done. files modified: {len(changed)}")
    if changed:
        for c in changed:
            print("  -", c)


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
