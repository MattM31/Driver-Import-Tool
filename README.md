# Driver Import Tool v0.9

A modern Windows utility for exporting and importing hardware drivers using PowerShell and `pnputil.exe`. Built in Python 3.13, this tool offers both a user-friendly graphical interface and a powerful command-line mode — ideal for school IT departments, deployment techs, and sysadmins working with reimaging workflows.

---

## 💡 Key Features

- 📦 Export drivers from a machine using `Export-WindowsDriver`
- 📥 Import drivers `.inf` files recursively using `pnputil /install`
- 🧠 Intelligent retry logic for network driver installs
- 🖥️ GUI mode with a modern Windows 10/11 look
- 💻 Console mode for integration with automation tools like FOG
- 🧾 Log file support (customisable, default includes PC name)
- 🛡️ Administrator rights check and warning

---

## 🖥️ GUI Mode

Just run the `.exe` or `.py` file directly (no switches) and you’ll be greeted with a tabbed interface for **Import**, **Export**, and **Help**.

### Features:
- Folder selection for export/import
- Custom log file location support
- Live command-line output in the window
- Help tab with usage instructions
- Version display: `Driver Import Tool v0.9`

### Screenshot: 

---

## 💻 Console Mode

For scripting or remote execution, run with the `-console` flag:

```powershell
DriverImportTool.exe -console -import "C:\Drivers\LenovoM74"
DriverImportTool.exe -console -export "C:\Drivers\HPEliteDesk"
DriverImportTool.exe -console -import "C:\Drivers\Dell" -logFilePath "D:\Logs\CustomImportLog.log"
