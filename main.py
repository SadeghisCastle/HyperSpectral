import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import json
import DataMeasurer as dm
import numpy as np
import os
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import io
import sys

# --- Detect if we are in a PyInstaller-built executable ---
IS_FROZEN = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

if IS_FROZEN:
    # Suppress print() and error output in GUI executable
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

# --- Globals for plotting and scan control ---
plot_fig = None
plot_ax = None
plot_line = None
scan_data = []
scan_wls = []
scan_stopped = False

# --- Backend subprocess call ---
def run(command, *args):
    cmd = [
        r"C:/Users/Nanophotonics/AppData/Local/Programs/Python/Python310-32/python.exe",
        "C:/Users/Nanophotonics/Desktop/HyperSpectral/controller/spectrograph_command.py",
        command
    ] + list(map(str, args))

    startupinfo = None
    if IS_FROZEN:
        # Prevent console window from flashing open
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=45,
            startupinfo=startupinfo
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"MS260i command '{command}' timed out.")

    if result.returncode != 0:
        raise RuntimeError(f"Error running MS260i: {result.stderr.strip()}")

    output = result.stdout.strip()
    print(output)  # Safe in dev, suppressed in packaged GUI
    return output

# --- GUI Logic ---
def browse_save_location():
    filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if filepath:
        save_location_entry.delete(0, tk.END)
        save_location_entry.insert(0, filepath)

def start_scan():
    global scan_data, scan_wls, scan_stopped
    scan_stopped = False
    try:
        start_wl = float(start_entry.get())
        end_wl = float(end_entry.get())
        step_size = int(step_entry.get())
        save_path = save_location_entry.get()

        if not save_path:
            messagebox.showerror("Error", "Please select a save location.")
            return

        scan_wls = np.linspace(start_wl, end_wl, step_size + 1)
        scan_data = []

        run("goto", start_wl)
        time.sleep(5)
        run("open_shutter")

        def step_loop(index=0):
            if scan_stopped or index >= len(scan_wls):
                run("close_shutter")
                if not scan_stopped:
                    np.savetxt(save_path, np.column_stack([scan_wls, scan_data]), delimiter=",", header="Wavelength,Intensity", comments='')
                return

            wl = scan_wls[index]
            run("goto", wl)
            intensity = dm.record()
            scan_data.append(intensity)
            update_live_plot()
            root.after(100, lambda: step_loop(index + 1))

        root.after(0, step_loop)

    except ValueError:
        messagebox.showerror("Input Error", "Start/End wavelengths and step size must be numbers.")
    except Exception as e:
        messagebox.showerror("Unexpected Error", str(e))

def threaded_scan():
    threading.Thread(target=start_scan).start()

def stop_scan():
    global scan_stopped
    scan_stopped = True

def initialize_live_plot():
    global plot_fig, plot_ax, plot_line

    if plot_fig is None:
        plot_fig, plot_ax = plt.subplots()
        plot_line, = plot_ax.plot([], [], 'b-')
        plot_ax.set_xlabel("Wavelength (nm)")
        plot_ax.set_ylabel("Lock-In Amp Voltage")
        plot_ax.set_title("Live Data")
        plot_ax.grid(True)

        canvas = FigureCanvasTkAgg(plot_fig, master=plot_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plot_fig.tight_layout()

    else:
        plot_ax.clear()
        plot_ax.set_xlabel("Wavelength (nm)")
        plot_ax.set_ylabel("Lock-In Amp Voltage")
        plot_ax.set_title("Live Data")
        plot_ax.grid(True)
        plot_line, = plot_ax.plot([], [], 'b-')
        plot_fig.canvas.draw()

def update_live_plot():
    if plot_line:
        plot_line.set_data(scan_wls[:len(scan_data)], scan_data)
        plot_ax.relim()
        plot_ax.autoscale_view()
        plot_fig.canvas.draw()

def start_scan_with_plot():
    initialize_live_plot()
    threaded_scan()

def set_wavelength():
    set_wl = float(wl_entry.get())
    run("goto", set_wl)

def open_shutter():
    run("open_shutter")

def close_shutter():
    run("close_shutter")

def get_wav():
    try:
        wavelength = run("position")
        current_wavelength_label.config(text=f"Current Wavelength: {wavelength}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# --- GUI Layout ---
root = tk.Tk()
root.title("HyperSpectral")
root.geometry("1200x700")
root.resizable(True, True)

# --- Scan Settings Section ---
scan_frame = tk.LabelFrame(root, text="Scan Settings", padx=10, pady=10)
scan_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

tk.Label(scan_frame, text="Start Wavelength (nm):").grid(row=0, column=0, sticky="e")
tk.Label(scan_frame, text="End Wavelength (nm):").grid(row=1, column=0, sticky="e")
tk.Label(scan_frame, text="Step Count:").grid(row=2, column=0, sticky="e")
tk.Label(scan_frame, text="Save Location:").grid(row=3, column=0, sticky="e")

start_entry = tk.Entry(scan_frame)
end_entry = tk.Entry(scan_frame)
step_entry = tk.Entry(scan_frame)
save_location_entry = tk.Entry(scan_frame, width=30)

start_entry.grid(row=0, column=1, padx=5, pady=5)
end_entry.grid(row=1, column=1, padx=5, pady=5)
step_entry.grid(row=2, column=1, padx=5, pady=5)
save_location_entry.grid(row=3, column=1, padx=5, pady=5)

browse_button = tk.Button(scan_frame, text="Browse...", command=browse_save_location)
browse_button.grid(row=3, column=2, padx=5)

go_button = tk.Button(scan_frame, text="Start Scan", command=start_scan_with_plot, bg="green", fg="white", width=15)
go_button.grid(row=4, column=0, columnspan=2, pady=10)

stop_button = tk.Button(scan_frame, text="Stop Scan", command=stop_scan, bg="red", fg="white", width=15)
stop_button.grid(row=4, column=2, pady=10)

# --- Wavelength Controls Section ---
wl_frame = tk.LabelFrame(root, text="Wavelength Control", padx=10, pady=10)
wl_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

tk.Label(wl_frame, text="Set Wavelength:").grid(row=0, column=0, sticky="e")
wl_entry = tk.Entry(wl_frame)
wl_entry.grid(row=0, column=1, padx=5)

set_wl_button = tk.Button(wl_frame, text="Set", command=set_wavelength, bg="green", fg="white")
set_wl_button.grid(row=0, column=2, padx=5)

get_wavelength_button = tk.Button(wl_frame, text="Get Wavelength", command=get_wav, bg="green", fg="white")
get_wavelength_button.grid(row=1, column=0, columnspan=3, pady=5)

current_wavelength_label = tk.Label(wl_frame, text="Current Wavelength: --")
current_wavelength_label.grid(row=2, column=0, columnspan=3)

# --- Shutter Controls Section ---
shutter_frame = tk.LabelFrame(root, text="Shutter Control", padx=10, pady=10)
shutter_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

open_shutter_button = tk.Button(shutter_frame, text="Open Shutter", command=open_shutter, bg="green", fg="white")
open_shutter_button.grid(row=0, column=0, padx=5)

close_shutter_button = tk.Button(shutter_frame, text="Close Shutter", command=close_shutter, bg="green", fg="white")
close_shutter_button.grid(row=0, column=1, padx=5)

# --- Plot Area ---
plot_frame = tk.LabelFrame(root, text="Live Plot", padx=10, pady=10)
plot_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="nsew")

# --- Make GUI resizable ---
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
plot_frame.columnconfigure(0, weight=1)
plot_frame.rowconfigure(0, weight=1)

# --- Launch GUI ---
root.mainloop()
