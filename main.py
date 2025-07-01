import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import json
import DataMeasurer as dm
import numpy as np
import matplotlib.pyplot as plt
import os
from tkinter.scrolledtext import ScrolledText
import sys
import io
import threading

class TextRedirector(io.TextIOBase):
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        self.widget.configure(state='normal')
        self.widget.insert(tk.END, text)
        self.widget.see(tk.END)
        self.widget.configure(state='disabled')

    def flush(self):
        pass  # Not needed

def run(command, *args):
    cmd = [r"C:/Users/Nanophotonics/AppData/Local/Programs/Python/Python310-32/python.exe", "C:/Users/Nanophotonics/Desktop/HyperSpectral/controller/spectrograph_command.py", command] + list(map(str, args))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Error running MS260i: {result.stderr.strip()}")

    print(result.stdout.strip())

def browse_save_location():
    filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if filepath:
        save_location_entry.delete(0, tk.END)
        save_location_entry.insert(0, filepath)

def start_scan():
    try:
        start_wl = float(start_entry.get())
        end_wl = float(end_entry.get())
        step_size = int(step_entry.get())
        save_path = save_location_entry.get()

        if not save_path:
            messagebox.showerror("Error", "Please select a save location.")
            return

        wls = np.linspace(start_wl, end_wl, step_size+1)
        data = []
        associated_wl = []

        run("open_shutter")

        #try:
        for wl in wls:
            print(wl)
            run("goto", wl)
            print('wahoo')
            data.append(dm.record())
            print('weehee')
            associated_wl.append(wl)
            print('woohoo')

        run("close_shutter")

        # Save CSV
        np.savetxt(save_path, np.column_stack([associated_wl, data]), delimiter=",", header="Wavelength,Intensity", comments='')

        root.after(0, show_plot, associated_wl, data)

    except ValueError:
        messagebox.showerror("Input Error", "Start/End wavelengths and step size must be numbers.")
    except Exception as e:
        messagebox.showerror("Unexpected Error", str(e))

def threaded_scan():
    threading.Thread(target=start_scan).start()

def set_wavelength():
    set_wl = float(wl_entry.get())

    run("goto", set_wl)

def open_shutter():
    run("open_shutter")

def close_shutter():
    run("close_shutter")

def get_wav():
    run("position")

# --- GUI Layout ---

def show_plot(wls, data):
    # Plot
        plt.figure()
        plt.plot(wls, data)
        plt.ylim(bottom=-1, top=10)
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Measured Data")
        plt.title("Spectrograph Data")
        plt.grid(True)
        plt.show()

root = tk.Tk()
root.title("YeeHaw")

tk.Label(root, text="Start Wavelength (nm):").grid(row=0, column=0, sticky="e")
tk.Label(root, text="End Wavelength (nm):").grid(row=1, column=0, sticky="e")
tk.Label(root, text="Step Count:").grid(row=2, column=0, sticky="e")
tk.Label(root, text="Save Location:").grid(row=3, column=0, sticky="e")
tk.Label(root, text="Set Wavelength:").grid(row=0, column=2, sticky="e")

start_entry = tk.Entry(root)
end_entry = tk.Entry(root)
step_entry = tk.Entry(root)
wl_entry = tk.Entry(root)
save_location_entry = tk.Entry(root, width=30)

start_entry.grid(row=0, column=1, padx=5, pady=5)
end_entry.grid(row=1, column=1, padx=5, pady=5)
step_entry.grid(row=2, column=1, padx=5, pady=5)
wl_entry.grid(row=0, column=3, padx=5, pady=5)
save_location_entry.grid(row=3, column=1, padx=5, pady=5)

browse_button = tk.Button(root, text="Browse...", command=browse_save_location)
browse_button.grid(row=3, column=2, padx=5)

go_button = tk.Button(root, text="Start Scan", command=threaded_scan, bg="green", fg="white")
go_button.grid(row=4, column=0, columnspan=3, pady=15)

set_wl_button = tk.Button(root, text="Set", command=set_wavelength, bg="green", fg="white")
set_wl_button.grid(row=1, column=2, columnspan=3, pady=15)

open_shutter_button = tk.Button(root, text="Open shutter", command=open_shutter, bg="green", fg="white")
open_shutter_button.grid(row=6, column=3, columnspan=3, pady=15)

close_shutter_button = tk.Button(root, text="Close shutter", command=close_shutter, bg="green", fg="white")
close_shutter_button.grid(row=7, column=3, columnspan=3, pady=15)

root.mainloop()
