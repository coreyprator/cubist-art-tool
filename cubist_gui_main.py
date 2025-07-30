"""
Cubist Art Generator GUI

__version__ = "v12d"
__author__ = "Corey Prator"
__date__ = "2025-07-27"
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from cubist_core_logic import run_cubist
import traceback
import logging

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "last_config.txt")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "run_log.txt")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error_log.txt")

# Configure logging
logger = logging.getLogger("cubist_gui")
logger.setLevel(logging.INFO)

# File handler for all logs
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# File handler for errors only
error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
error_handler.setFormatter(error_formatter)
logger.addHandler(error_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

logger.info("Starting Program")



def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            for k, v in config.items():
                f.write(f"{k}={v}\n")
        logger.info("Config saved.")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

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
            "clip_to_alpha": str(clip_to_alpha)
        }

        save_config(config)
        logger.info(f"START: {config}")
        result_path = run_cubist(input_path, output_dir, mask_path, total_points, clip_to_alpha)
        logger.info(f"SUCCESS: {result_path}")

        if messagebox.askyesno("Success", f"Output saved to: {result_path}. View it?"):
            os.startfile(result_path)
    except Exception as e:
        logger.error(f"ERROR: {traceback.format_exc()}")
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
                if '=' in line:
                    k, v = line.strip().split("=", 1)
                    config[k.strip()] = v.strip()
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
        clip_to_alpha.set(int(config["clip_to_alpha"]) if config["clip_to_alpha"] in ["0", "1"] else int(config["clip_to_alpha"].lower() == "true"))
    logger.info("Last config loaded.")



# Restore missing input fields and labels
tk.Label(root, text="Input Image:").grid(row=0, column=0, sticky="e")
input_entry = tk.Entry(root, width=50)
input_entry.grid(row=0, column=1)
tk.Button(root, text="Browse", command=lambda: browse_file(input_entry)).grid(row=0, column=2)

tk.Label(root, text="Output Dir:").grid(row=1, column=0, sticky="e")
output_entry = tk.Entry(root, width=50)
output_entry.grid(row=1, column=1)
tk.Button(root, text="Browse", command=lambda: browse_dir(output_entry)).grid(row=1, column=2)

tk.Label(root, text="Mask Image:").grid(row=2, column=0, sticky="e")
mask_entry = tk.Entry(root, width=50)
mask_entry.grid(row=2, column=1)
tk.Button(root, text="Browse", command=lambda: browse_file(mask_entry)).grid(row=2, column=2)

tk.Label(root, text="Total Points:").grid(row=3, column=0, sticky="e")
points_entry = tk.Entry(root, width=10)
points_entry.grid(row=3, column=1, sticky="w")

clip_var = tk.IntVar(value=1)
tk.Checkbutton(root, text="Clip to Alpha/Mask", variable=clip_var).grid(row=4, column=1, sticky="w")

# Restore previous session values after widgets are created
load_last_config(input_entry, output_entry, mask_entry, points_entry, clip_var)

tk.Button(root, text="Generate", command=run_process).grid(row=5, column=1)

root.mainloop()



# Version v12d | Timestamp: 2025-07-27 17:32 UTC | Hash: <SHA256>