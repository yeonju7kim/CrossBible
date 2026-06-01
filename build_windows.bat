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
python -c "from PIL import Image; Image.open('assets/icon.png').save('assets/icon.ico', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
if errorlevel 1 (
    echo [ERROR] Icon conversion failed
    pause
    exit /b 1
)

echo [4/4] Running PyInstaller...
pyinstaller --clean --noconfirm ^
    --windowed ^
    --name CrossBible ^
    --icon assets/icon.ico ^
    --add-data "assets/icon.png;assets" ^
    --collect-submodules PyQt6 ^
    main.py
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo ==========================================
echo  Build complete!
echo  Output: dist\CrossBible\CrossBible.exe
echo ==========================================
echo.
pause
