# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: archive/cubist_gui_main.py
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:30+02:00
# === CUBIST STAMP END ===


import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
from cubist_core_logic import run_cubist_pipeline

CONFIG_PATH = "cubist_last_config.json"

def load_last_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
            return config
        except:
            pass
    return {}

def save_last_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)

def run_cubist():
    input_path = input_entry.get()
    output_dir = output_entry.get()
    mask_path = mask_entry.get()
    try:
        total_points = int(points_entry.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Point count must be an integer.")
        return

    clip = clip_var.get() == 1
    use_mask = use_mask_var.get() == 1

    config = {
        "input_path": input_path,
        "output_dir": output_dir,
        "total_points": total_points,
        "clip_to_alpha": clip,
        "mask_path": mask_path if use_mask else None
    }

    save_last_config(config)
    result_path = run_cubist_pipeline(**config)

    if result_path:
        if messagebox.askyesno("Success", f"Art generated at:
{result_path}

View it?"):
            try:
                subprocess.Popen(['xdg-open' if os.name == 'posix' else 'start', result_path], shell=True)
            except Exception as e:
                messagebox.showerror("Error", str(e))

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

last = load_last_config()

tk.Label(root, text="Input Image:").grid(row=0, column=0, sticky="e")
input_entry = tk.Entry(root, width=50)
input_entry.insert(0, last.get("input_path", ""))
input_entry.grid(row=0, column=1)
tk.Button(root, text="Browse", command=lambda: browse_file(input_entry)).grid(row=0, column=2)

tk.Label(root, text="Output Folder:").grid(row=1, column=0, sticky="e")
output_entry = tk.Entry(root, width=50)
output_entry.insert(0, last.get("output_dir", ""))
output_entry.grid(row=1, column=1)
tk.Button(root, text="Browse", command=lambda: browse_dir(output_entry)).grid(row=1, column=2)

tk.Label(root, text="Object Mask (Optional):").grid(row=2, column=0, sticky="e")
mask_entry = tk.Entry(root, width=50)
mask_entry.insert(0, last.get("mask_path", ""))
mask_entry.grid(row=2, column=1)
tk.Button(root, text="Browse", command=lambda: browse_file(mask_entry)).grid(row=2, column=2)

use_mask_var = tk.IntVar(value=1 if last.get("mask_path") else 0)
tk.Checkbutton(root, text="Use Mask", variable=use_mask_var).grid(row=2, column=3, sticky="w")

tk.Label(root, text="Total Points:").grid(row=3, column=0, sticky="e")
points_entry = tk.Entry(root, width=10)
points_entry.insert(0, str(last.get("total_points", 1000)))
points_entry.grid(row=3, column=1, sticky="w")

clip_var = tk.IntVar(value=1 if last.get("clip_to_alpha", True) else 0)
tk.Checkbutton(root, text="Clip to Alpha", variable=clip_var).grid(row=3, column=2, sticky="w")

tk.Button(root, text="Generate", command=run_cubist).grid(row=4, column=1, pady=10)

root.mainloop()


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:30+02:00
# === CUBIST FOOTER STAMP END ===
