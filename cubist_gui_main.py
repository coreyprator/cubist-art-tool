# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: cubist_gui_main.py
# Version: v2.3.4
# Build: 2025-09-01T08:25:00
# Commit: n/a
# Stamped: 2025-09-01T08:36:03
# === CUBIST STAMP END ===
# ======================================================================
# File: cubist_gui_main.py
# Stamp: 2025-08-22T17:31:37Z
# (Auto-added header for paste verification)
# ======================================================================
"""
Cubist Art Generator GUI

Usage:
    python cubist_gui_main.py

- Launches a simple Tkinter GUI for generating Cubist Art images.
- Lets you select input image, output directory, mask image, and point count.
- Remembers your last-used settings between runs.
- Click "Generate" to run the core logic and produce output.
- This GUI always runs the default geometry mode (usually 'delaunay') as implemented by run_cubist in cubist_core_logic.py.
- It was written as a basic test, and is not the main GUI for production use.

__version__ = "v12d"
__author__ = "Corey Prator"
__date__ = "2025-07-27"
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
from cubist_logger import log_message
from cubist_core_logic import run_cubist
import traceback

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "last_config.txt")

log_message("Starting Program")


def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            for k, v in config.items():
                f.write(f"{k}={v}\n")
        log_message("Config saved.")
    except Exception as e:
        log_message(f"Failed to save config: {e}", level="error")


def run_process():
    try:
        input_path = input_entry.get()
        output_dir = output_entry.get()
        mask_path = mask_entry.get()
        total_points = int(points_entry.get())
        clip_to_alpha = bool(clip_var.get())

        config = {
            "input_path": input_path,
            "output_dir": output_dir,
            "mask_path": mask_path,
            "total_points": str(total_points),
            "clip_to_alpha": str(clip_to_alpha),
        }

        save_config(config)
        log_message(f"START: {config}")
        result_path = run_cubist(
            input_path, output_dir, mask_path, total_points, clip_to_alpha
        )
        log_message(f"SUCCESS: {result_path}")

        if messagebox.askyesno("Success", f"Output saved to: {result_path}. View it?"):
            os.startfile(result_path)
    except Exception as e:
        log_message(f"ERROR: {traceback.format_exc()}", level="error")
        messagebox.showerror("Error", f"An error occurred:\n{e}")


def browse_file(entry):
    filename = filedialog.askopenfilename()
    if filename:
        entry.delete(0, tk.END)
        entry.insert(0, filename)


def browse_dir(entry):
    dirname = filedialog.askdirectory()
    if dirname:
        entry.delete(0, tk.END)
        entry.insert(0, dirname)


root = tk.Tk()
root.title("Cubist Art Generator")


def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    config[k.strip()] = v.strip()
        log_message("Last config loaded.")
    return config


def load_last_config(input_path, output_dir, mask_path, total_points, clip_to_alpha):
    config = load_config()
    if "input_path" in config:
        input_path.delete(0, tk.END)
        input_path.insert(0, config["input_path"])
    if "output_dir" in config:
        output_dir.delete(0, tk.END)
        output_dir.insert(0, config["output_dir"])
    if "mask_path" in config:
        mask_path.delete(0, tk.END)
        mask_path.insert(0, config["mask_path"])
    if "total_points" in config:
        total_points.delete(0, tk.END)
        total_points.insert(0, config["total_points"])
    if "clip_to_alpha" in config:
        clip_to_alpha.set(
            int(config["clip_to_alpha"])
            if config["clip_to_alpha"] in ["0", "1"]
            else int(config["clip_to_alpha"].lower() == "true")
        )
    log_message("Last config loaded.")


# Restore missing input fields and labels
tk.Label(root, text="Input Image:").grid(row=0, column=0, sticky="e")
input_entry = tk.Entry(root, width=50)
input_entry.grid(row=0, column=1)
tk.Button(root, text="Browse", command=lambda: browse_file(input_entry)).grid(
    row=0, column=2
)

tk.Label(root, text="Output Dir:").grid(row=1, column=0, sticky="e")
output_entry = tk.Entry(root, width=50)
output_entry.grid(row=1, column=1)
tk.Button(root, text="Browse", command=lambda: browse_dir(output_entry)).grid(
    row=1, column=2
)

tk.Label(root, text="Mask Image:").grid(row=2, column=0, sticky="e")
mask_entry = tk.Entry(root, width=50)
mask_entry.grid(row=2, column=1)
tk.Button(root, text="Browse", command=lambda: browse_file(mask_entry)).grid(
    row=2, column=2
)

tk.Label(root, text="Total Points:").grid(row=3, column=0, sticky="e")
points_entry = tk.Entry(root, width=10)
points_entry.grid(row=3, column=1, sticky="w")

clip_var = tk.IntVar(value=1)
tk.Checkbutton(root, text="Clip to Alpha/Mask", variable=clip_var).grid(
    row=4, column=1, sticky="w"
)

# Restore previous session values after widgets are created
load_last_config(input_entry, output_entry, mask_entry, points_entry, clip_var)

tk.Button(root, text="Generate", command=run_process).grid(row=5, column=1)

root.mainloop()


# Version v12d | Timestamp: 2025-07-27 17:32 UTC | Hash: <SHA256>
# ======================================================================
# End of File: cubist_gui_main.py  (2025-08-22T17:31:37Z)
# ======================================================================
# === CUBIST FOOTER STAMP BEGIN ===
# End of file — v2.3.4 — stamped 2025-09-01T08:36:03
# === CUBIST FOOTER STAMP END ===
