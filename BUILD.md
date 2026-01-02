# Build Instructions

To export this application as a standalone executable (`.exe` or `.app`), you must run the build command on the **same operating system** you want to target.

**Note:** You cannot build a Windows `.exe` on a Mac, or a Mac `.app` on Windows.

## 1. Prerequisites (All OS)
- Python 3.10 or newer
- Install project dependencies:
  ```bash
  pip install -r requirements.txt
  pip install pyinstaller
  ```

## 2. Build for Windows
1. Copy this project folder to a Windows PC.
2. Double-click the included `build_windows.bat` file.
3. **OR** Run this command in Command Prompt:
   ```bash
   pyinstaller --noconfirm --onedir --windowed --name "IIT KGP ERP Manager" --icon "assets/logo.png" --add-data "assets;assets" --add-data "src;src" --collect-all customtkinter main.py
   ```
4. Output: `dist\IIT KGP ERP Manager\IIT KGP ERP Manager.exe`

## 3. Build for Mac (macOS)
1. Open Terminal in the project folder.
2. Run:
   ```bash
   pyinstaller --noconfirm --onedir --windowed --name "IIT KGP ERP Manager" --icon "assets/logo.png" --add-data "assets:assets" --add-data "src:src" --collect-all customtkinter main.py
   ```
3. Output: `dist/IIT KGP ERP Manager.app`

## 4. Build for Linux
1. Open Terminal.
2. Run:
   ```bash
   pyinstaller --noconfirm --onedir --windowed --name "erp_manager" --icon "assets/logo.png" --add-data "assets:assets" --add-data "src:src" --collect-all customtkinter main.py
   ```
3. Output: `dist/erp_manager` (binary)
