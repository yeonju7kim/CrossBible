@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo  CrossBible  Windows Build (PyInstaller)
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo         Install Python 3.10+ from https://www.python.org/downloads/
    echo         IMPORTANT: check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Virtual env
if not exist .venv (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo [2/4] Installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install pyinstaller Pillow -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)

echo [3/4] Converting icon.png to icon.ico (for the exe)...
if exist assets\icon.ico del /f /q assets\icon.ico
python -c "from PIL import Image; img = Image.open('assets/icon.png').convert('RGBA'); img.save('assets/icon.ico', format='ICO', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])"
if errorlevel 1 (
    echo [ERROR] Icon conversion failed
    pause
    exit /b 1
)
if not exist assets\icon.ico (
    echo [ERROR] assets\icon.ico was not produced
    pause
    exit /b 1
)

echo [4/4] Running PyInstaller (clean build)...
if exist dist\CrossBible rmdir /s /q dist\CrossBible
if exist build\CrossBible rmdir /s /q build\CrossBible
pyinstaller --clean --noconfirm ^
    --windowed ^
    --name CrossBible ^
    --icon "assets\icon.ico" ^
    --add-data "assets\icon.png;assets" ^
    --add-data "assets\icon.ico;assets" ^
    --add-data "version.txt;." ^
    --collect-submodules PyQt6 ^
    main.py
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed
    pause
    exit /b 1
)

REM Windows Explorer/taskbar caches exe icons aggressively; nudge the shell
REM so the new icon shows up without a reboot.
ie4uinit.exe -show >nul 2>&1

echo.
echo ==========================================
echo  Build complete!
echo  Output: dist\CrossBible\CrossBible.exe
echo.
echo  If the .exe icon still looks like the old one in Explorer,
echo  it's the Windows icon cache. Try one of:
echo    - move the dist\CrossBible folder somewhere else, then back
echo    - log off and back in
echo    - delete %%LOCALAPPDATA%%\IconCache.db and restart Explorer
echo ==========================================
echo.
pause
