# Driver Import Tool v0.9
# Python 3.13 compatible
import os
import subprocess
import socket
import time
import ctypes
import argparse
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# --- Constants ---
PC_NAME = socket.gethostname()
DEFAULT_LOG_PATH = f"C:\\DriverImporter-{PC_NAME}.log"
RETRY_ATTEMPTS = 3
RETRY_DELAY = 10

# --- Utilities ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def log_message(log_path, message, console=None):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp} {message}\n")
    if console:
        console.insert(tk.END, f"{timestamp} {message}\n")
        console.see(tk.END)
    else:
        print(f"{timestamp} {message}")

def run_command(command, log_path, console=None):
    process = subprocess.Popen(["powershell", "-Command", command],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        log_message(log_path, line.strip(), console)
    process.wait()
    return process.returncode

def export_drivers(destination_path, log_path, console=None):
    os.makedirs(destination_path, exist_ok=True)
    command = f"Export-WindowsDriver -Online -Destination \"{destination_path}\""
    log_message(log_path, f"Starting export to {destination_path}", console)
    returncode = run_command(command, log_path, console)
    log_message(log_path, f"Export finished with exit code {returncode}", console)

def import_drivers(source_path, log_path, console=None):
    all_inf_paths = []
    net_inf_paths = []

    for root, _, files in os.walk(source_path):
        for file in files:
            if file.lower().endswith(".inf"):
                full_path = os.path.join(root, file)
                if "net" in file.lower() or "network" in file.lower():
                    net_inf_paths.append(full_path)
                else:
                    all_inf_paths.append(full_path)

    combined_paths = all_inf_paths + net_inf_paths
    log_message(log_path, f"Found {len(combined_paths)} driver files to import.", console)

    for inf_file in combined_paths:
        attempt = 0
        while attempt < RETRY_ATTEMPTS:
            if os.path.exists(inf_file):
                command = f'pnputil /add-driver "{inf_file}" /install'
                log_message(log_path, f"Installing driver: {inf_file}", console)
                returncode = run_command(command, log_path, console)
                if returncode == 0:
                    break
                else:
                    log_message(log_path, f"Error installing {inf_file}, retrying...", console)
            else:
                log_message(log_path, f"Path not found: {inf_file}, retrying in {RETRY_DELAY}s...", console)
            attempt += 1
            time.sleep(RETRY_DELAY)

        if attempt == RETRY_ATTEMPTS:
            log_message(log_path, f"Failed to install after {RETRY_ATTEMPTS} attempts: {inf_file}", console)

# --- GUI ---
def start_gui():
    def select_folder(entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def select_log(entry):
        path = filedialog.asksaveasfilename(defaultextension=".log",
                                            initialfile=f"DriverImporter-{PC_NAME}.log")
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def run_export():
        folder = export_path.get()
        logfile = export_log.get()
        if not folder:
            messagebox.showerror("Missing Info", "Please select an export folder")
            return
        export_drivers(folder, logfile, console)

    def run_import():
        folder = import_path.get()
        logfile = import_log.get()
        if not folder:
            messagebox.showerror("Missing Info", "Please select an import folder")
            return
        import_drivers(folder, logfile, console)

    root = tk.Tk()
    root.title("Driver Import Tool")
    root.geometry("750x500")
    if not is_admin():
        messagebox.showwarning("Admin Rights", "Warning: This tool is not running as Administrator. Functions may fail.")

    nb = ttk.Notebook(root)
    frame_import = ttk.Frame(nb)
    frame_export = ttk.Frame(nb)
    frame_help = ttk.Frame(nb)

    nb.add(frame_import, text="Import")
    nb.add(frame_export, text="Export")
    nb.add(frame_help, text="Help")
    nb.pack(expand=True, fill='both')

    for frame, path_var, log_var, label in [
        (frame_import, tk.StringVar(), tk.StringVar(value=DEFAULT_LOG_PATH), "Import From"),
        (frame_export, tk.StringVar(), tk.StringVar(value=DEFAULT_LOG_PATH), "Export To")
    ]:
        ttk.Label(frame, text=f"{label} Folder:").pack(pady=5)
        path_entry = ttk.Entry(frame, textvariable=path_var, width=70)
        path_entry.pack()
        ttk.Button(frame, text="Browse", command=lambda e=path_entry: select_folder(e)).pack(pady=2)

        ttk.Label(frame, text="Log File Path:").pack(pady=5)
        log_entry = ttk.Entry(frame, textvariable=log_var, width=70)
        log_entry.pack()
        ttk.Button(frame, text="Browse", command=lambda e=log_entry: select_log(e)).pack(pady=2)

        ttk.Button(frame, text="Start", command=run_import if label == "Import From" else run_export).pack(pady=10)

    global import_path, import_log, export_path, export_log, console
    import_path, import_log = path_var, log_var
    export_path, export_log = path_var, log_var

    console = scrolledtext.ScrolledText(root, height=12, bg="black", fg="white")
    console.pack(fill='x', padx=5, pady=5)

    help_text = """
--- GUI Mode ---
1. Use the Import or Export tab.
2. Select your folder and log file location.
3. Click Start to run the process.

--- Console Mode ---
Run the tool from command line:
  DriverImportTool.exe -console -import "C:\\Path" -logFilePath "C:\\log.txt"
  DriverImportTool.exe -console -export "C:\\Path" (uses default log if not provided)

Note: Network drivers are installed last to reduce risk of connection dropouts.
Admin rights are required for full functionality.
    """
    ttk.Label(frame_help, text=help_text, justify="left").pack(padx=10, pady=10, anchor="w")
    ttk.Label(root, text="Version 0.9").pack(side="bottom", anchor="e", padx=10, pady=5)

    root.mainloop()

# --- CLI ---
def start_console():
    parser = argparse.ArgumentParser()
    parser.add_argument("-console", action="store_true")
    parser.add_argument("-import", dest="import_path", type=str, help="Path to import drivers from")
    parser.add_argument("-export", dest="export_path", type=str, help="Path to export drivers to")
    parser.add_argument("-logFilePath", dest="log_file", type=str, default=DEFAULT_LOG_PATH)
    args = parser.parse_args()

    if args.import_path:
        import_drivers(args.import_path, args.log_file)
    elif args.export_path:
        export_drivers(args.export_path, args.log_file)
    else:
        print("Missing -import or -export path")

# --- Entry Point ---
if __name__ == "__main__":
    import sys
    if "-console" in sys.argv:
        start_console()
    else:
        start_gui()
