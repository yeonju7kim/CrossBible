@echo off
REM CrossBible Windows 빌드 (PyInstaller 단일 exe)
REM 사용 전: python -m pip install -r requirements.txt pyinstaller

pyinstaller ^
  --noconfirm ^
  --windowed ^
  --name CrossBible ^
  --collect-submodules PyQt6 ^
  main.py
