# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: archive/cubist_gui.py
# Version: v2.3.7
# Build: 2025-09-01T11:23:56
# Commit: f01b715
# Stamped: 2025-09-01T11:23:59+02:00
# === CUBIST STAMP END ===

import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
from cubist_main_v7_refactored import run_cubist

CONFIG_PATH = "last_session_config.json"


def save_last_session(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)


def load_last_session():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            if not os.path.exists(config.get("input_path", "")):
                config["input_path"] = ""
            if not os.path.exists(config.get("output_dir", "")):
                config["output_dir"] = ""
            return config
    return {}


def browse_input(entry):
    path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]
    )
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)


def browse_output(entry):
    path = filedialog.askdirectory()
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)


def launch_viewer(image_path):
    try:
        subprocess.run(["start", image_path], check=False, shell=True)
    except Exception as e:
        print(f"Could not open viewer: {e}")


def run_app():
    input_path = entry_input.get()
    output_dir = entry_output.get()
    try:
        total_points = int(entry_points.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Total points must be an integer.")
        return
    clip_to_alpha = clip_var.get()

    if not os.path.isfile(input_path):
        messagebox.showerror("Error", "Invalid input image path.")
        return
    if not os.path.isdir(output_dir):
        messagebox.showerror("Error", "Invalid output directory.")
        return

    run_cubist(
        input_path, output_dir, total_points=total_points, clip_to_alpha=clip_to_alpha
    )

    suffix = f"{total_points:05d}"
    output_image = os.path.join(output_dir, f"frame_01_{suffix}pts.png")
    if os.path.exists(output_image):
        if messagebox.askyesno("Done", "Processing complete. View output image?"):
            launch_viewer(output_image)

    save_last_session(
        {
            "input_path": input_path,
            "output_dir": output_dir,
            "total_points": total_points,
            "clip_to_alpha": clip_to_alpha,
        }
    )


# === UI ===
root = tk.Tk()
root.title("Cubist Generator UI")

session = load_last_session()

tk.Label(root, text="Input Image:").grid(row=0, column=0, sticky="e")
entry_input = tk.Entry(root, width=50)
entry_input.grid(row=0, column=1)
entry_input.insert(0, session.get("input_path", ""))
tk.Button(root, text="Browse", command=lambda: browse_input(entry_input)).grid(
    row=0, column=2
)

tk.Label(root, text="Output Directory:").grid(row=1, column=0, sticky="e")
entry_output = tk.Entry(root, width=50)
entry_output.grid(row=1, column=1)
entry_output.insert(0, session.get("output_dir", ""))
tk.Button(root, text="Browse", command=lambda: browse_output(entry_output)).grid(
    row=1, column=2
)

tk.Label(root, text="Total Points:").grid(row=2, column=0, sticky="e")
entry_points = tk.Entry(root, width=10)
entry_points.grid(row=2, column=1, sticky="w")
entry_points.insert(0, session.get("total_points", 1000))

clip_var = tk.BooleanVar(value=session.get("clip_to_alpha", True))
tk.Checkbutton(root, text="Clip to Alpha", variable=clip_var).grid(
    row=3, column=1, sticky="w"
)

tk.Button(root, text="Run", command=run_app).grid(row=4, column=1, pady=10)

root.mainloop()



# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:23:59+02:00
# === CUBIST FOOTER STAMP END ===
