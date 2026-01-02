@echo off
echo ==========================================
echo IIT KGP ERP Manager - Windows Builder
echo ==========================================

echo Step 1: Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Step 2: Building erp.exe...
:: Windows uses ; for path separators in PyInstaller
pyinstaller --noconfirm --onedir --windowed --name "erp" --icon "assets/logo.png" --add-data "assets;assets" --add-data "src;src" --collect-all customtkinter main.py

echo.
echo ==========================================
echo Build Complete!
echo You can run the app from: dist\erp\erp.exe
echo ==========================================
pause
