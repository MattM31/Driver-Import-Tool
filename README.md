# Driver Import Tool v0.9

A modern Windows utility for exporting and importing hardware drivers using PowerShell and `pnputil.exe`. Built in Python 3.13, this tool offers both a user-friendly graphical interface and a powerful command-line mode — ideal for school IT departments, deployment techs, and sysadmins working with reimaging workflows.

---

## 💡 Key Features

* 📦 Export drivers from a machine using `Export-WindowsDriver`
* 📅 Import drivers `.inf` files recursively using `pnputil /install`
* 🧠 Intelligent retry logic for network driver installs
* 🖥️ GUI mode with a modern Windows 10/11 look
* 💻 Console mode for integration with automation tools like FOG
* 🗞️ Log file support (customisable, default includes PC name)
* 🛡️ Administrator rights check and warning

---

## 🖥️ GUI Mode

Just run the `.exe` or `.py` file directly (no switches) and you’ll be greeted with a tabbed interface for **Import**, **Export**, and **Help**.

### Features:

* Folder selection for export/import
* Custom log file location support
* Live command-line output in the window
* Help tab with usage instructions
* Version display: `Driver Import Tool v0.9`

---

## 💻 Console Mode

For scripting or remote execution, run with the `-console` flag:

```powershell
DriverImportTool.exe -console -import "C:\Drivers\LenovoM74"
DriverImportTool.exe -console -export "C:\Drivers\HPEliteDesk"
DriverImportTool.exe -console -import "C:\Drivers\Dell" -logFilePath "D:\Logs\CustomImportLog.log"
DriverImportTool.exe -console -export "C:\Drivers\HP" -nolog
DriverImportTool.exe -console -importAuto "\\10.20.8.226\Drivers$"
```

If `-logFilePath` is omitted, logs are saved to:

```
C:\DriverImporter-{PCNAME}.log
```
Use `-nolog` to skip creating a log file.

---

## ⚙️ Installation / Usage

### 🔹 Requirements

* Windows 10 / 11
* Admin rights required for full functionality
* Python 3.13+ (if using from source)
* `pyinstaller` (for packaging)

### 🔹 Run from Source

```bash
python DriverImportTool.py
```

### 🔹 Build Executable

To package into a `.exe`:

```bash
pyinstaller --noconfirm --onefile --windowed DriverImportTool.py
```

Console mode now opens its own window when the `-console` flag is used, so you
can keep the `--windowed` option.

---

## 🗑️ Logging

Each action is logged with a timestamp. You can view or archive the `.log` file for auditing purposes. Network connectivity errors are noted, including retries.

---

## 📌 Notes

* Network drivers are automatically installed **last** during import to reduce the risk of disconnecting the PC mid-process.
* If a `.inf` file fails due to temporary loss of access (e.g., network drop), the app retries it 3 times with a 10-second pause between.
* This tool does **not** rely on any non-standard Python packages — ideal for clean deployments.

---

## 📃 Licence

MIT Licence – you are free to use, modify, and distribute.

---

## 💠 Future Plans

* Add support for exporting by specific driver classes
* Dark mode GUI toggle
* System tray background option for remote install monitoring
* Optional auto-retry toggle in GUI
* Drag-and-drop folder support
* Scheduled import/export (GUI timer)

---

## 👤 Author

Developed by **Matt Morton**
For support or suggestions, open an issue or contact via GitHub.
