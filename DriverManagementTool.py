# Driver Import Tool v0.9
# Python 3.13 compatible
import os
import subprocess
import threading
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
    """Log a message to file and optionally update the GUI console.

    Any errors encountered while writing to the log file are reported back to the
    console in red text but do not interrupt execution."""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_line = f"{timestamp} {message}\n"
    if log_path:
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(log_line)
        except Exception as e:  # PermissionError or other IO issues
            err_msg = "Error: Incorrect Permissions" if isinstance(e, PermissionError) else f"Error writing log: {e}"
            err_line = f"{timestamp} {err_msg}\n"
            if console:
                if callable(console):
                    console(err_line, "error")
                else:
                    console.insert(tk.END, err_line, "error")
                    console.see(tk.END)
            else:
                print(err_line, end="")
    if console:
        if callable(console):
            console(log_line)
        else:
            console.insert(tk.END, log_line)
            console.see(tk.END)
    else:
        print(log_line, end="")

def prepare_log(log_path, console=None):
    """Ensure the log file can be created. Return usable path or None."""
    if not log_path:
        return None
    try:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8"):
            pass
        return log_path
    except Exception as e:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        err = f"{timestamp} Error: Cannot create log file '{log_path}': {e}\n"
        if console:
            if callable(console):
                console(err, "error")
            else:
                console.insert(tk.END, err, "error")
                console.see(tk.END)
        else:
            print(err, end="")
        return None

def run_command(command, log_path, console=None):
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW

    process = subprocess.Popen([
            "powershell",
            "-NoProfile",
            "-Command",
            command
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=creationflags
    )
    for line in process.stdout:
        log_message(log_path, line.strip(), console)
    process.wait()
    return process.returncode

def run_command_filtered(command, log_path, console=None, error_filter=None):
    """Run command and only output lines to console that match the error_filter."""
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW

    process = subprocess.Popen([
            "powershell",
            "-NoProfile",
            "-Command",
            command
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=creationflags
    )
    for line in process.stdout:
        stripped = line.strip()
        log_message(log_path, stripped)
        if console and error_filter and error_filter(stripped):
            console(f"{stripped}\n", "error")
    process.wait()
    return process.returncode

def export_drivers(destination_path, log_path, console=None):
    os.makedirs(destination_path, exist_ok=True)
    command = f"Export-WindowsDriver -Online -Destination \"{destination_path}\""
    log_message(log_path, f"Starting export to {destination_path}", console)
    if console:
        console("Running export command...\n")

    def is_error(line: str) -> bool:
        return "error" in line.lower() or "failed" in line.lower()

    returncode = run_command_filtered(command, log_path, console, is_error)
    log_message(log_path, f"Export finished with exit code {returncode}", console)
    return returncode

def import_drivers(source_path, log_path, console=None):

    all_inf_paths = []
    net_inf_paths = []

    for root, _, files in os.walk(source_path):
        for file in files:
            if file.lower().endswith(".inf"):
                full_path = os.path.normpath(os.path.join(root, file))

                if "net" in file.lower() or "network" in file.lower():
                    net_inf_paths.append(full_path)
                else:
                    all_inf_paths.append(full_path)


    combined_paths = all_inf_paths + net_inf_paths
    log_message(log_path, f"Found {len(combined_paths)} driver files to import.", console)


    any_failed = False

    for inf_file in combined_paths:
        attempt = 0

        while attempt < RETRY_ATTEMPTS and not os.path.exists(inf_file):
            log_message(log_path, f"Path not found: {inf_file}, retrying in {RETRY_DELAY}s...", console)

            attempt += 1
            time.sleep(RETRY_DELAY)

        if not os.path.exists(inf_file):
            log_message(log_path, f"Failed to find path after {RETRY_ATTEMPTS} attempts: {inf_file}", console)
            any_failed = True
            continue

        command = f'pnputil /add-driver "{inf_file}" /install'
        log_message(log_path, f"Installing driver: {inf_file}", console)
        returncode = run_command(command, log_path, console)
        if returncode != 0:
            log_message(log_path, f"Error installing {inf_file}: exit code {returncode}", console)
            any_failed = True

    final_code = 0 if not any_failed else 1
    log_message(log_path, f"Import finished with exit code {final_code}", console)
    return final_code


# --- GUI ---
def start_gui():

    def select_folder(entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)

            entry.insert(0, os.path.normpath(path))


    def select_log(entry):
        path = filedialog.asksaveasfilename(defaultextension=".log",
                                            initialfile=f"DriverImporter-{PC_NAME}.log")
        if path:
            entry.delete(0, tk.END)

            entry.insert(0, os.path.normpath(path))


    def run_export():
        folder = os.path.normpath(export_path_var.get())
        logfile = None if export_nolog_var.get() else os.path.normpath(export_log_var.get())
        logfile = prepare_log(logfile, append_console)
        if not folder:
            messagebox.showerror("Missing Info", "Please select an export folder")
            return

        start_export_btn.config(state=tk.DISABLED)
        progress.start()

        def task():
            try:
                export_drivers(folder, logfile, append_console)
            except Exception as e:
                err_msg = f"Error: {e}"
                append_console(err_msg + "\n", "error")
                log_message(logfile, err_msg, append_console)
            finally:
                progress.after(0, lambda: (
                    progress.stop(),
                    start_export_btn.config(state=tk.NORMAL)
                ))

        threading.Thread(target=task, daemon=True).start()

    def run_import():
        folder = os.path.normpath(import_path_var.get())
        logfile = None if import_nolog_var.get() else os.path.normpath(import_log_var.get())
        logfile = prepare_log(logfile, append_console)
        if not folder:
            messagebox.showerror("Missing Info", "Please select an import folder")
            return

        start_import_btn.config(state=tk.DISABLED)
        progress.start()

        def task():
            try:
                import_drivers(folder, logfile, append_console)
            except Exception as e:
                err_msg = f"Error: {e}"
                append_console(err_msg + "\n", "error")
                log_message(logfile, err_msg, append_console)
            finally:
                progress.after(0, lambda: (
                    progress.stop(),
                    start_import_btn.config(state=tk.NORMAL)
                ))

        threading.Thread(target=task, daemon=True).start()

    root = tk.Tk()
    root.title("Driver Management Tool")
    root.geometry("750x500")
    root.iconbitmap("DriverManagementTool.ico")

    
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

    import_path_var = tk.StringVar()
    import_log_var = tk.StringVar(value=DEFAULT_LOG_PATH)
    export_path_var = tk.StringVar()
    export_log_var = tk.StringVar(value=DEFAULT_LOG_PATH)
    import_nolog_var = tk.IntVar(value=0)
    export_nolog_var = tk.IntVar(value=0)

    # Import Tab Widgets
    ttk.Label(frame_import, text="Import From Folder:").pack(pady=5)
    import_path_entry = ttk.Entry(frame_import, textvariable=import_path_var, width=70)
    import_path_entry.pack()
    ttk.Button(frame_import, text="Browse", command=lambda e=import_path_entry: select_folder(e)).pack(pady=2)

    ttk.Label(frame_import, text="Log File Path:").pack(pady=5)
    import_log_entry = ttk.Entry(frame_import, textvariable=import_log_var, width=70)
    import_log_entry.pack()
    import_log_browse = ttk.Button(frame_import, text="Browse", command=lambda e=import_log_entry: select_log(e))
    import_log_browse.pack(pady=2)
    def toggle_import_log():
        state = tk.DISABLED if import_nolog_var.get() else tk.NORMAL
        import_log_entry.config(state=state)
        import_log_browse.config(state=state)

    ttk.Checkbutton(frame_import, text="Don't use a log file", variable=import_nolog_var,
                    command=toggle_import_log).pack(pady=2)

    start_import_btn = ttk.Button(frame_import, text="Start", command=run_import)
    start_import_btn.pack(pady=10)

    # Export Tab Widgets
    ttk.Label(frame_export, text="Export To Folder:").pack(pady=5)
    export_path_entry = ttk.Entry(frame_export, textvariable=export_path_var, width=70)
    export_path_entry.pack()
    ttk.Button(frame_export, text="Browse", command=lambda e=export_path_entry: select_folder(e)).pack(pady=2)

    ttk.Label(frame_export, text="Log File Path:").pack(pady=5)
    export_log_entry = ttk.Entry(frame_export, textvariable=export_log_var, width=70)
    export_log_entry.pack()
    export_log_browse = ttk.Button(frame_export, text="Browse", command=lambda e=export_log_entry: select_log(e))
    export_log_browse.pack(pady=2)
    def toggle_export_log():
        state = tk.DISABLED if export_nolog_var.get() else tk.NORMAL
        export_log_entry.config(state=state)
        export_log_browse.config(state=state)

    ttk.Checkbutton(frame_export, text="Don't use a log file", variable=export_nolog_var,
                    command=toggle_export_log).pack(pady=2)

    start_export_btn = ttk.Button(frame_export, text="Start", command=run_export)
    start_export_btn.pack(pady=10)

    console = scrolledtext.ScrolledText(root, height=12, bg="black", fg="white")
    console.pack(fill='x', padx=5, pady=5)
    console.tag_config('error', foreground='red')

    def append_console(text, tag=None):
        def _write():
            if tag:
                console.insert(tk.END, text, tag)
            else:
                console.insert(tk.END, text)
            console.see(tk.END)
        console.after(0, _write)

    progress = ttk.Progressbar(root, mode="indeterminate")
    progress.pack(fill='x', padx=5, pady=5)

    help_text = """
--- GUI Mode ---
1. Use the Import or Export tab.
2. Select your folder and log file location (or tick 'Don't use a log file').
3. Click Start to run the process.

--- Console Mode ---
Run the tool from command line:
  DriverImportTool.exe -console -import "C:\\Path" -logFilePath "C:\\log.txt"
  DriverImportTool.exe -console -export "C:\\Path" -nolog

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
    parser.add_argument("-nolog", action="store_true", help="Do not create a log file")
    args = parser.parse_args()

    log_file_path = os.path.normpath(args.log_file) if args.log_file else None
    log_file = None if args.nolog else prepare_log(log_file_path)

    try:
        if args.import_path:
            import_path = os.path.normpath(args.import_path)
            import_drivers(import_path, log_file)
        elif args.export_path:
            export_path = os.path.normpath(args.export_path)
            export_drivers(export_path, log_file)
        else:
            print("Missing -import or -export path")
    except Exception as e:
        err_msg = f"Error: {e}"
        log_message(log_file, err_msg)
        print(err_msg)

# --- Entry Point ---
if __name__ == "__main__":
    import sys
    if "-console" in sys.argv:
        start_console()
    else:
        start_gui()
