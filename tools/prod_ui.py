# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: tools/prod_ui.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:49+02:00
# === CUBIST STAMP END ===

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import versioning  # unified banner/version

# ---------------------------- Paths & constants -----------------------------

HERE = Path(__file__).resolve()
TOOLS_DIR = HERE.parent
REPO_ROOT = TOOLS_DIR.parent
CLI_WRAPPER = TOOLS_DIR / "run_cli.py"  # wrapper prints version banner
CLI_PATH = REPO_ROOT / "cubist_cli.py"  # kept for diagnostics
PLUGINS_DIR = REPO_ROOT / "geometry_plugins"
OUTPUT_ROOT = REPO_ROOT / "output" / "production"
CONFIGS_DIR = REPO_ROOT / "configs"
CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIGS_DIR / "prod_ui.json"
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "prod_ui.log"

# Hide plugins that aren't artistic/ready for production.
PLUGIN_BLACKLIST = {"concentric_circles"}

BUILTINS = ("delaunay", "voronoi", "rectangles")


def log(line: str) -> None:
    stamp = datetime.now().isoformat(timespec="seconds")
    text = f"{stamp} {line}"
    print(text, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        pass


def discover_plugins_safely() -> List[str]:
    """Import & list plugin names; never raise."""
    try:
        import geometry_registry as geom  # type: ignore

        try:
            geom.load_plugins(str(PLUGINS_DIR))
        except Exception as e:
            log(f"[prod_ui] load_plugins error: {e}")
        get_names = getattr(geom, "names", None)
        if callable(get_names):
            names = list(get_names())
        else:
            reg = getattr(geom, "_registry", {}) or getattr(geom, "_REGISTRY", {})
            names = sorted(reg.keys()) if isinstance(reg, dict) else []
        # Filter
        names = [n for n in names if n not in BUILTINS and n not in PLUGIN_BLACKLIST]
        return sorted(names)
    except Exception as e:
        log(f"[prod_ui] discover_plugins exception: {e}")
        return []


def ts_folder(root: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    p = root / stamp
    p.mkdir(parents=True, exist_ok=True)
    return p


def startfile_cross(path: str | Path) -> None:
    p = str(path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(p)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", p])
        else:
            subprocess.Popen(["xdg-open", p])
    except Exception as e:
        log(f"[prod_ui] startfile error: {e}")


def try_svg_to_png(
    svg_path: Path,
    png_path: Path,
    width_hint: Optional[int] = None,
    height_hint: Optional[int] = None,
) -> bool:
    """
    Best-effort rasterization of SVG -> PNG so production runs have both.
    Requires CairoSVG; if unavailable, we just return False.
    """
    try:
        import cairosvg  # type: ignore
    except Exception:
        log("[prod_ui] NOTE: CairoSVG not installed; skipping SVG->PNG rasterization.")
        return False
    try:
        png_path.parent.mkdir(parents=True, exist_ok=True)
        if width_hint and height_hint:
            cairosvg.svg2png(
                url=str(svg_path),
                write_to=str(png_path),
                output_width=width_hint,
                output_height=height_hint,
            )
        else:
            cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))
        return True
    except Exception as e:
        log(f"[prod_ui] CairoSVG failed: {e}")
        return False


class RunnerThread(threading.Thread):
    def __init__(
        self,
        queue_out: "queue.Queue[str]",
        selections: List[Tuple[str, bool]],  # (geometry, is_plugin)
        points: int,
        seed: Optional[int],
        cascade_stages: int,
        export_svg: bool,
        enable_plugin_exec: bool,
        input_image: Optional[str],
        output_root: Path,
        svg_passthrough: bool,
        input_svg: Optional[str],
    ):
        super().__init__(daemon=True)
        self.queue_out = queue_out
        self.selections = selections
        self.points = points
        self.seed = seed
        self.cascade_stages = cascade_stages
        self.export_svg = export_svg
        self.enable_plugin_exec = enable_plugin_exec
        self.input_image = input_image
        self.output_root = output_root
        self.svg_passthrough = svg_passthrough
        self.input_svg = input_svg

    def emit(self, line: str) -> None:
        try:
            self.queue_out.put_nowait(line.rstrip("\n"))
        except Exception:
            pass

    def run_one(self, geom: str, is_plugin: bool, out_dir: Path) -> int:
        py = sys.executable
        wrapper = (
            CLI_WRAPPER if CLI_WRAPPER.exists() else REPO_ROOT / "tools" / "run_cli.py"
        )
        cmd: List[str] = [py, str(wrapper)]
        if self.svg_passthrough and self.input_svg and geom == "svg":
            cmd += ["--input-svg", self.input_svg]
        else:
            if not self.input_image:
                self.emit(f"[{geom}] ERROR: No input image selected.")
                return 2
            cmd += ["--input", self.input_image]

        cmd += [
            "--output",
            str(out_dir),
            "--geometry",
            geom,
            "--points",
            str(self.points),
        ]
        if self.seed is not None:
            cmd += ["--seed", str(self.seed)]
        cmd += ["--cascade-stages", str(self.cascade_stages)]
        if self.export_svg:
            cmd += ["--export-svg"]
        if self.enable_plugin_exec and is_plugin:
            cmd += ["--enable-plugin-exec"]

        self.emit(f"[{geom}] RUN: {' '.join(cmd)}")
        try:
            proc = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
        except Exception as e:
            self.emit(f"[{geom}] EXCEPTION: {e}")
            return 2

        out = proc.stdout or ""
        for line in out.splitlines():
            self.emit(f"[{geom}] {line}")

        # Quick file audit
        try:
            pngs = sorted(list(out_dir.glob("*.png")))
            svgs = sorted(list(out_dir.glob("*.svg")))
            mets = sorted(list(out_dir.glob("*.json")))
            self.emit(
                f"[{geom}] files: png={len(pngs)} svg={len(svgs)} metrics={len(mets)}"
            )
            for p in pngs + svgs + mets:
                self.emit(f"[{geom}] -> {p}")
        except Exception:
            pngs, svgs = [], []

        # If no PNG but an SVG exists, try to rasterize SVG -> PNG (best-effort)
        if not pngs and svgs:
            guess = out_dir / f"{geom}.png"
            width_hint = None
            height_hint = None
            if self.input_image:
                try:
                    from PIL import Image  # type: ignore

                    with Image.open(self.input_image) as im:
                        width_hint, height_hint = im.size
                except Exception:
                    pass
            made = try_svg_to_png(svgs[0], guess, width_hint, height_hint)
            if made:
                self.emit(f"[{geom}] (post) SVG->PNG rasterized -> {guess}")

        return proc.returncode

    def run(self) -> None:
        out_root = ts_folder(OUTPUT_ROOT)
        self.emit(f"[ui] Output root: {out_root}")
        rc_any = 0
        for geom, is_plugin in self.selections:
            subdir = out_root / geom
            subdir.mkdir(parents=True, exist_ok=True)
            rc_any |= self.run_one(geom, is_plugin, subdir)
        if rc_any == 0:
            self.emit("[ui] COMPLETE successfully.")
        else:
            self.emit("[ui] COMPLETE with errors.")
        self.emit(f"[ui] OPEN_OUTPUT {out_root}")


class ProdUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # version banner at launch
        versioning.print_banner("prod_ui")

        self.title(f"Cubist Production Runner — {versioning.VERSION}")
        self.geometry("1000x650")
        self.minsize(900, 560)

        # state
        self.plugin_vars: Dict[str, tk.IntVar] = {}
        self.builtin_vars: Dict[str, tk.IntVar] = {
            b: tk.IntVar(value=1 if b == "delaunay" else 0) for b in BUILTINS
        }
        self.points_var = tk.StringVar(value="800")
        self.seed_var = tk.StringVar(value="123")
        self.cascade_var = tk.StringVar(value="3")
        self.export_svg_var = tk.IntVar(value=1)
        self.plugin_exec_var = tk.IntVar(value=1)
        self.input_img_var = tk.StringVar(value="")
        self.svg_passthrough_var = tk.IntVar(value=0)
        self.input_svg_var = tk.StringVar(value="")
        self.queue_out: "queue.Queue[str]" = queue.Queue()

        # UI
        self._build_ui()
        self._bind_keys()

        # show & bring front
        self.after(10, self._present)

        # async plugin scan and config load
        self.after(50, self._start_async_discovery)
        self.after(80, self._load_config_safe)
        self.after(100, self._poll_queue)

        # diags
        log(f"[prod_ui] repo_root={REPO_ROOT}")
        log(
            f"[prod_ui] cli_wrapper={'OK' if CLI_WRAPPER.exists() else 'MISSING'} -> {CLI_WRAPPER}"
        )
        log(
            f"[prod_ui] cli_path={'OK' if CLI_PATH.exists() else 'MISSING'} -> {CLI_PATH}"
        )
        log(
            f"[prod_ui] plugins_dir={'OK' if PLUGINS_DIR.exists() else 'MISSING'} -> {PLUGINS_DIR}"
        )
        log(f"[prod_ui] logs -> {LOG_FILE}")

    def _present(self):
        try:
            self.deiconify()
            try:
                self.eval("tk::PlaceWindow . center")
            except Exception:
                pass
            self.lift()
            self.attributes("-topmost", True)

            def _unset_topmost() -> None:
                self.attributes("-topmost", False)

            self.after(300, _unset_topmost)
            log("[prod_ui] window presented")
        except Exception as e:
            log(f"[prod_ui] present error: {e}")

    def _bind_keys(self):
        self.bind_all("<Control-Shift-s>", lambda _e: self._toggle_dev_panel())

    def _build_ui(self):
        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)

        g_in = ttk.LabelFrame(left, text="Input")
        g_in.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(g_in, text="Image:").grid(row=0, column=0, sticky="e")
        ttk.Entry(g_in, textvariable=self.input_img_var, width=50).grid(
            row=0, column=1, sticky="we", padx=4, pady=2
        )
        ttk.Button(g_in, text="Browse...", command=self._browse_image).grid(
            row=0, column=2, padx=2
        )

        g_params = ttk.LabelFrame(left, text="Parameters")
        g_params.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(g_params, text="Points:").grid(row=0, column=0, sticky="e")
        ttk.Entry(g_params, textvariable=self.points_var, width=9).grid(
            row=0, column=1, sticky="w", padx=4, pady=2
        )
        ttk.Label(g_params, text="Seed:").grid(row=1, column=0, sticky="e")
        ttk.Entry(g_params, textvariable=self.seed_var, width=9).grid(
            row=1, column=1, sticky="w", padx=4, pady=2
        )
        ttk.Label(g_params, text="Cascade Stages:").grid(row=2, column=0, sticky="e")
        ttk.Entry(g_params, textvariable=self.cascade_var, width=9).grid(
            row=2, column=1, sticky="w", padx=4, pady=2
        )
        ttk.Checkbutton(g_params, text="Export SVG", variable=self.export_svg_var).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=4
        )
        ttk.Checkbutton(
            g_params,
            text="Enable plugin exec (for plugins)",
            variable=self.plugin_exec_var,
        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=4)

        g_bi = ttk.LabelFrame(left, text="Built-in geometries")
        g_bi.pack(fill=tk.X, pady=(0, 8))
        for i, name in enumerate(BUILTINS):
            ttk.Checkbutton(g_bi, text=name, variable=self.builtin_vars[name]).grid(
                row=i, column=0, sticky="w"
            )

        g_pl = ttk.LabelFrame(left, text="Discovered plugins")
        g_pl.pack(fill=tk.BOTH, expand=False, pady=(0, 8))
        self.plugins_container = ttk.Frame(g_pl)
        self.plugins_container.pack(fill=tk.BOTH, expand=True)
        self.plugins_hint = ttk.Label(
            self.plugins_container, text="(Scanning plugins…)"
        )
        self.plugins_hint.pack(anchor="w")
        btn_row = ttk.Frame(g_pl)
        btn_row.pack(fill=tk.X)
        ttk.Button(
            btn_row, text="Refresh Plugins", command=self._start_async_discovery
        ).pack(side=tk.LEFT)
        ttk.Button(
            btn_row, text="Select All", command=lambda: self._select_plugins(True)
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(
            btn_row, text="Select None", command=lambda: self._select_plugins(False)
        ).pack(side=tk.LEFT)

        g_act = ttk.LabelFrame(left, text="Actions")
        g_act.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(g_act, text="Run Selected", command=self.run_selected).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(
            g_act, text="Open Output Folder", command=self.open_output_root
        ).pack(fill=tk.X, pady=2)
        ttk.Button(g_act, text="Save Config", command=self.save_config).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(g_act, text="Load Config", command=self.load_config).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(
            g_act, text="Clean Production Outputs…", command=self.clean_outputs
        ).pack(fill=tk.X, pady=2)

        self.dev_frame = ttk.LabelFrame(
            left, text="Dev: SVG Passthrough (Ctrl+Shift+S)"
        )
        ttk.Checkbutton(
            self.dev_frame,
            text="Use SVG passthrough (geometry=svg)",
            variable=self.svg_passthrough_var,
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(self.dev_frame, text="Input SVG:").grid(row=1, column=0, sticky="e")
        ttk.Entry(self.dev_frame, textvariable=self.input_svg_var, width=42).grid(
            row=1, column=1, sticky="w", padx=4
        )
        ttk.Button(self.dev_frame, text="Browse...", command=self._browse_svg).grid(
            row=1, column=2, padx=2
        )

        right = ttk.Frame(self)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.log = tk.Text(right, wrap="word", state="disabled")
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(right, orient="vertical", command=self.log.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.configure(yscrollcommand=vsb.set)

        self.status = ttk.Label(self, text="Ready.", anchor="w")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _toggle_dev_panel(self):
        if getattr(self, "dev_svg_visible", False):
            self.dev_frame.pack_forget()
            self.dev_svg_visible = False
        else:
            self.dev_frame.pack(fill=tk.X, pady=(0, 8))
            self.dev_svg_visible = True

    def _select_plugins(self, val: bool):
        for var in self.plugin_vars.values():
            var.set(1 if val else 0)

    def _browse_image(self):
        fpath = filedialog.askopenfilename(
            title="Select input image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff;*.webp;*.*")],
        )
        if fpath:
            self.input_img_var.set(fpath)

    def _browse_svg(self):
        fpath = filedialog.askopenfilename(
            title="Select input SVG",
            filetypes=[("SVG", "*.svg"), ("All files", "*.*")],
        )
        if fpath:
            self.input_svg_var.set(fpath)

    def append_log(self, line: str):
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def set_status(self, msg: str):
        self.status.configure(text=msg)

    def _poll_queue(self):
        try:
            while True:
                line = self.queue_out.get_nowait()
                if line.startswith("[ui] OPEN_OUTPUT "):
                    _, _, p = line.partition("OPEN_OUTPUT ")
                    self._last_output_root = p.strip()
                else:
                    self.append_log(line)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _start_async_discovery(self):
        self.plugins_hint.configure(text="(Scanning plugins…)")

        def worker():
            names = discover_plugins_safely()
            self.after(0, lambda: self._apply_plugins(names))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_plugins(self, names: List[str]):
        for child in self.plugins_container.winfo_children():
            child.destroy()
        self.plugin_vars.clear()
        if not names:
            ttk.Label(self.plugins_container, text="(No plugins found)").pack(
                anchor="w"
            )
        else:
            for name in names:
                var = tk.IntVar(value=0)
                self.plugin_vars[name] = var
                ttk.Checkbutton(self.plugins_container, text=name, variable=var).pack(
                    anchor="w"
                )
        log(f"[prod_ui] plugins={names}")

    def _load_config_safe(self):
        try:
            self.load_config()
        except Exception as e:
            log(f"[prod_ui] load_config error: {e}")

    def _collect_selections(self) -> List[Tuple[str, bool]]:
        sel: List[Tuple[str, bool]] = []
        for name, var in self.builtin_vars.items():
            if var.get():
                sel.append((name, False))
        for name, var in self.plugin_vars.items():
            if var.get():
                sel.append((name, True))
        if self.svg_passthrough_var.get():
            sel.append(("svg", False))
        return sel

    def run_selected(self):
        if not CLI_PATH.exists():
            messagebox.showerror("Error", f"CLI not found: {CLI_PATH}")
            return

        try:
            pts = int(self.points_var.get().strip())
            cas = int(self.cascade_var.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Points and Cascade Stages must be integers.")
            return
        seed_str = self.seed_var.get().strip()
        seed = int(seed_str) if seed_str else None

        selections = self._collect_selections()
        if not selections:
            messagebox.showinfo(
                "Nothing to run", "Select at least one geometry or plugin."
            )
            return

        need_image = (
            any(g != "svg" for g, _ in selections) or not self.svg_passthrough_var.get()
        )
        if need_image and not self.input_img_var.get().strip():
            messagebox.showerror("Error", "Please choose an input image.")
            return
        if self.svg_passthrough_var.get() and not self.input_svg_var.get().strip():
            messagebox.showerror(
                "Error", "SVG passthrough is enabled but no input SVG selected."
            )
            return

        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.set_status("Running…")
        with self.queue_out.mutex:
            self.queue_out.queue.clear()

        runner = RunnerThread(
            queue_out=self.queue_out,
            selections=selections,
            points=pts,
            seed=seed,
            cascade_stages=cas,
            export_svg=bool(self.export_svg_var.get()),
            enable_plugin_exec=bool(self.plugin_exec_var.get()),
            input_image=self.input_img_var.get().strip() or None,
            output_root=OUTPUT_ROOT,
            svg_passthrough=bool(self.svg_passthrough_var.get()),
            input_svg=self.input_svg_var.get().strip() or None,
        )
        runner.start()

        def waiter():
            while runner.is_alive():
                time.sleep(0.2)
            self.set_status("Done.")

        threading.Thread(target=waiter, daemon=True).start()

    def open_output_root(self):
        base = OUTPUT_ROOT
        if base.exists():
            subdirs = [p for p in base.iterdir() if p.is_dir()]
            if subdirs:
                subdirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                startfile_cross(subdirs[0])
                return
        startfile_cross(base)

    def clean_outputs(self):
        base = OUTPUT_ROOT
        if not base.exists():
            messagebox.showinfo("Nothing to clean", f"{base} does not exist.")
            return
        ok = messagebox.askyesno(
            "Confirm clean",
            f"Delete ALL contents under:\n{base}\n\nThis cannot be undone.",
        )
        if not ok:
            return
        import shutil

        try:
            shutil.rmtree(base)
            base.mkdir(parents=True, exist_ok=True)
            self.append_log("[ui] Cleaned production outputs.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clean outputs:\n{e}")

    def save_config(self):
        cfg = {
            "input_img": self.input_img_var.get(),
            "points": self.points_var.get(),
            "seed": self.seed_var.get(),
            "cascade": self.cascade_var.get(),
            "export_svg": int(self.export_svg_var.get()),
            "plugin_exec": int(self.plugin_exec_var.get()),
            "builtins": {k: int(v.get()) for k, v in self.builtin_vars.items()},
            "plugins": {k: int(v.get()) for k, v in self.plugin_vars.items()},
            "svg_passthrough": int(self.svg_passthrough_var.get()),
            "input_svg": self.input_svg_var.get(),
        }
        try:
            CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            self.set_status(f"Saved config to {CONFIG_PATH}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config:\n{e}")

    def load_config(self):
        if not CONFIG_PATH.exists():
            return
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        self.input_img_var.set(cfg.get("input_img", ""))
        self.points_var.set(str(cfg.get("points", "800")))
        self.seed_var.set(str(cfg.get("seed", "123")))
        self.cascade_var.set(str(cfg.get("cascade", "3")))
        self.export_svg_var.set(int(cfg.get("export_svg", 1)))
        self.plugin_exec_var.set(int(cfg.get("plugin_exec", 1)))
        for k, v in cfg.get("builtins", {}).items():
            if k in self.builtin_vars:
                self.builtin_vars[k].set(int(v))
        # plugin selections are applied after the next discovery


def main():
    versioning.print_banner("prod_ui-entry")
    app = ProdUI()
    app.mainloop()


if __name__ == "__main__":
    main()


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:49+02:00
# === CUBIST FOOTER STAMP END ===
