@echo off
title Lumi Editor — Build System (.exe)
echo ========================================================
echo           LUMI EDITOR — EXECUTABLE BUILDER
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Verifying Python and dependencies...
python -m pip install -r requirements.txt pyinstaller > nul 2>&1

echo [2/3] Generating icon asset...
python -c "from PIL import Image; img = Image.open('assets/logo.png'); img.save('assets/logo.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"

echo [3/3] Compiling standalone LumiEditor.exe...
python -m PyInstaller --onefile --windowed --name "LumiEditor" --icon=NONE --add-data "assets;assets" main.py

echo.
if exist "dist\LumiEditor.exe" (
    echo ========================================================
    echo  SUCCESS: Standalone executable created!
    echo  Location: "%~dp0dist\LumiEditor.exe"
    echo ========================================================
) else (
    echo [ERROR] Build failed. Please check the logs above.
)

echo.
pause
