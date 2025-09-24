import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

def select_input():
    path = filedialog.askopenfilename(
        title="Select input LAS file",
        filetypes=[("LAS files", "*.las"), ("All files", "*.*")]
    )
    if path:
        input_var.set(path)

def select_output():
    path = filedialog.asksaveasfilename(
        title="Select output HTML file",
        defaultextension=".html",
        filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
    )
    if path:
        output_var.set(path)

def create_report():
    input_path = input_var.get()
    output_path = output_var.get()
    
    # Basic checks
    if not os.path.isfile(input_path):
        messagebox.showerror("Error", f"Input file does not exist:\n{input_path}")
        return
    if not output_path:
        messagebox.showerror("Error", "Please specify an output HTML file.")
        return

    # Normalize slashes for R
    input_r = input_path.replace("\\", "/")
    output_r = output_path.replace("\\", "/")
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "R", "pointcloud_analyses.rmd"
        ).replace("\\", "/")

    # Build Rscript command
    cmd = [
        "Rscript", "-e",
        f"rmarkdown::render('{script_path}', "
        f"params = list(src = '{input_r}'), "
        f"output_file = '{output_r}')"
    ]

    try:
        subprocess.run(cmd, check=True)
        messagebox.showinfo("Success", f"Report created:\n{output_path}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to create report.\n{e}")

def cancel():
    root.destroy()

# Create GUI
root = tk.Tk()
root.title("LiDAR R Markdown Report")

input_var = tk.StringVar()
output_var = tk.StringVar()

tk.Label(root, text="Input LAS file:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
tk.Entry(root, textvariable=input_var, width=50).grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Browse...", command=select_input).grid(row=0, column=2, padx=5, pady=5)

tk.Label(root, text="Output HTML file:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
tk.Entry(root, textvariable=output_var, width=50).grid(row=1, column=1, padx=5, pady=5)
tk.Button(root, text="Browse...", command=select_output).grid(row=1, column=2, padx=5, pady=5)

tk.Button(root, text="Create report", command=create_report, bg="green", fg="white").grid(row=2, column=1, sticky="e", padx=5, pady=15)
tk.Button(root, text="Cancel", command=cancel, bg="red", fg="white").grid(row=2, column=2, sticky="w", padx=5, pady=15)

root.mainloop()