# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: archive/cubist_ui_launcher.py
# Version: v2.3.7
# Build: 2025-09-01T13:31:41
# Commit: 8163630
# Stamped: 2025-09-01T13:31:46+02:00
# === CUBIST STAMP END ===

import tkinter as tk
from tkinter import filedialog, messagebox
from cubist_main_v7_refactored import run_cubist


def browse_file(entry):
    path = filedialog.askopenfilename()
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)


def browse_folder(entry):
    path = filedialog.askdirectory()
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)


def run_wrapper():
    input_path = input_entry.get()
    output_dir = output_entry.get()
    try:
        total_points = int(points_entry.get())
        clip = clip_var.get()
        run_cubist(
            input_path, output_dir, total_points=total_points, clip_to_alpha=clip
        )
        messagebox.showinfo("Success", "Cubist art generation completed.")
    except Exception as e:
        messagebox.showerror("Error", str(e))


root = tk.Tk()
root.title("Cubist Art Generator")

tk.Label(root, text="Input Image Path:").grid(row=0, column=0, sticky="e")
input_entry = tk.Entry(root, width=50)
input_entry.grid(row=0, column=1)
tk.Button(root, text="Browse", command=lambda: browse_file(input_entry)).grid(
    row=0, column=2
)

tk.Label(root, text="Output Directory:").grid(row=1, column=0, sticky="e")
output_entry = tk.Entry(root, width=50)
output_entry.grid(row=1, column=1)
tk.Button(root, text="Browse", command=lambda: browse_folder(output_entry)).grid(
    row=1, column=2
)

tk.Label(root, text="Total Points:").grid(row=2, column=0, sticky="e")
points_entry = tk.Entry(root)
points_entry.insert(0, "1000")
points_entry.grid(row=2, column=1)

clip_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Clip to Alpha", variable=clip_var).grid(
    row=3, column=1, sticky="w"
)

tk.Button(root, text="Run Cubist Generator", command=run_wrapper).grid(
    row=4, column=1, pady=10
)

root.mainloop()




# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T13:31:46+02:00
# === CUBIST FOOTER STAMP END ===
