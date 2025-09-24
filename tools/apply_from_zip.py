from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import time
import zipfile

# --- Utilities ---------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def count_lines_bytes(data: bytes) -> int:
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


# --- Core -------------------------------------------------------------------


class ApplyReport:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, **kw) -> None:
        self.items.append(kw)

    def print(self) -> None:
        for it in self.items:
            print(
                f"WROTE {it['path']} lines={it['lines']} sha256={it['sha256']}"
                if it.get("wrote")
                else f"SKIP  {it['path']} (dry-run) lines={it['lines']} sha256={it['sha256']}"
            )
        ok = all(it.get("verify_ok", True) for it in self.items)
        print("---")
        print(
            f"Applied {sum(it.get('wrote', False) for it in self.items)} files; verify={ok}"
        )


def load_manifest(zf: zipfile.ZipFile) -> dict | None:
    try:
        with zf.open("manifest.json") as f:
            return json.load(f)
    except KeyError:
        return None


def apply_zip(
    zip_path: Path, root: Path, backup: bool, verify: bool, dry_run: bool
) -> ApplyReport:
    report = ApplyReport()
    root = root.resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        manifest = load_manifest(zf)
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            if name.endswith("/"):
                continue
            if name == "manifest.json":
                continue
            if name.startswith("__MACOSX/"):
                continue

            data = zf.read(info)
            sha = sha256_bytes(data)
            lines = count_lines_bytes(data)

            if manifest:
                m = manifest.get(name)
                if m and m.get("sha256") and m["sha256"] != sha:
                    print(
                        f"WARNING: manifest sha mismatch for {name}: {m['sha256']} != {sha}"
                    )

            out_path = root / name
            if dry_run:
                report.add(
                    path=rel(out_path, root), wrote=False, lines=lines, sha256=sha
                )
                continue

            ensure_parent(out_path)
            if backup and out_path.exists():
                ts = time.strftime("%Y%m%d-%H%M%S")
                backup_root = root / ".backup" / ts
                backup_path = backup_root / name
                ensure_parent(backup_path)
                shutil.copy2(out_path, backup_path)

            with open(out_path, "wb") as f:
                f.write(data)
            wrote_sha = sha256_file(out_path)
            verify_ok = wrote_sha == sha
            if verify and not verify_ok:
                print(
                    f"ERROR: sha mismatch after write for {name}: {wrote_sha} != {sha}"
                )
            report.add(
                path=rel(out_path, root),
                wrote=True,
                lines=lines,
                sha256=wrote_sha,
                verify_ok=verify_ok,
            )
    return report


# --- Self-test --------------------------------------------------------------

DEMO_ZIP_BYTES: bytes | None = None


def build_demo_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        files = {
            "tools/HELLO.txt": b"hello from bundle\n",
            "tools/codebundle_apply.py": (
                b"# minimal stub for future bundles\n"
                b"print('codebundle_apply: installed')\n"
            ),
            "README.txt": b"This is a demo bundle.\n",
        }
        manifest: dict[str, dict] = {}
        for name, data in files.items():
            zf.writestr(name, data)
            manifest[name] = {
                "sha256": sha256_bytes(data),
                "lines": count_lines_bytes(data),
            }
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
    return buf.getvalue()


# lazily build demo once
if DEMO_ZIP_BYTES is None:
    DEMO_ZIP_BYTES = build_demo_zip()


def write_temp_demo_zip() -> Path:
    tmp = Path(tempfile.gettempdir()) / f"bundle_demo_{int(time.time())}.zip"
    with open(tmp, "wb") as f:
        f.write(DEMO_ZIP_BYTES)
    return tmp


# --- CLI --------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Apply a code bundle ZIP with SHA256 + line-count verification."
    )
    p.add_argument("zip", nargs="?", help="Path to bundle zip (omit with --selftest)")
    p.add_argument(
        "--root", default=".", help="Project root to write into (default: .)"
    )
    p.add_argument(
        "--backup",
        action="store_true",
        help="Back up overwritten files under ./.backup/<ts>/",
    )
    p.add_argument(
        "--verify", action="store_true", help="Verify SHA256 after write (recommended)"
    )
    p.add_argument("--dry-run", action="store_true", help="Don't write, just report")
    p.add_argument(
        "--selftest",
        action="store_true",
        help="Create a demo zip and apply it to --root",
    )
    args = p.parse_args(argv)

    if args.selftest:
        zp = write_temp_demo_zip()
        print(f"[selftest] demo zip: {zp}")
        zpath = zp
    else:
        if not args.zip:
            p.error("zip path required (or use --selftest)")
        zpath = Path(args.zip)
        if not zpath.exists():
            p.error(f"zip not found: {zpath}")

    root = Path(args.root).resolve()
    report = apply_zip(
        Path(zpath), root, backup=args.backup, verify=args.verify, dry_run=args.dry_run
    )
    report.print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
