@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo  CrossBible  Windows Launcher (no build)
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

REM Virtual env lives in the app cache folder (~/.crossbible), not the project dir.
set "CB_CACHE=%USERPROFILE%\.crossbible"
set "CB_VENV=%CB_CACHE%\.venv"
if not exist "%CB_CACHE%" mkdir "%CB_CACHE%"
if not exist "%CB_VENV%" (
    echo [1/3] Creating virtual environment in %CB_VENV% ...
    python -m venv "%CB_VENV%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )

    echo [2/3] Installing dependencies (first run only)...
    call "%CB_VENV%\Scripts\activate.bat"
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] pip install failed
        pause
        exit /b 1
    )
) else (
    call "%CB_VENV%\Scripts\activate.bat"
)

echo [3/3] Launching CrossBible...
echo.
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] CrossBible exited with an error.
    pause
)
