#!/usr/bin/env bash
# CrossBible — macOS 빌드 (PyInstaller). 실행: bash build_mac.sh  (또는 chmod +x 후 ./build_mac.sh)
set -euo pipefail
cd "$(dirname "$0")"

echo "=========================================="
echo "  CrossBible  macOS Build (PyInstaller)"
echo "=========================================="
echo

# Python 3 확인
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found."
    echo "        Install Python 3.10+ from https://www.python.org/downloads/"
    echo "        (or: brew install python)"
    exit 1
fi

# 가상환경
if [ ! -d .venv ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv .venv
fi

echo "[2/4] Installing dependencies..."
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pyinstaller -r requirements.txt

echo "[3/4] Converting icon.png to icon.icns (for the .app)..."
ICONSET="assets/icon.iconset"
rm -rf "$ICONSET" assets/icon.icns
mkdir -p "$ICONSET"
# macOS 표준 iconset 세트 (sips 로 각 크기 생성 → iconutil 로 .icns 패킹)
sips -z 16 16     assets/icon.png --out "$ICONSET/icon_16x16.png"      >/dev/null
sips -z 32 32     assets/icon.png --out "$ICONSET/icon_16x16@2x.png"   >/dev/null
sips -z 32 32     assets/icon.png --out "$ICONSET/icon_32x32.png"      >/dev/null
sips -z 64 64     assets/icon.png --out "$ICONSET/icon_32x32@2x.png"   >/dev/null
sips -z 128 128   assets/icon.png --out "$ICONSET/icon_128x128.png"    >/dev/null
sips -z 256 256   assets/icon.png --out "$ICONSET/icon_128x128@2x.png" >/dev/null
sips -z 256 256   assets/icon.png --out "$ICONSET/icon_256x256.png"    >/dev/null
sips -z 512 512   assets/icon.png --out "$ICONSET/icon_256x256@2x.png" >/dev/null
sips -z 512 512   assets/icon.png --out "$ICONSET/icon_512x512.png"    >/dev/null
sips -z 1024 1024 assets/icon.png --out "$ICONSET/icon_512x512@2x.png" >/dev/null
iconutil -c icns "$ICONSET" -o assets/icon.icns
rm -rf "$ICONSET"
if [ ! -f assets/icon.icns ]; then
    echo "[ERROR] assets/icon.icns was not produced"
    exit 1
fi

echo "[4/4] Running PyInstaller (clean build)..."
rm -rf dist/CrossBible.app build/CrossBible
# macOS 는 --add-data 구분자가 ':' (윈도우는 ';')
pyinstaller --clean --noconfirm \
    --windowed \
    --name CrossBible \
    --icon "assets/icon.icns" \
    --add-data "assets/icon.png:assets" \
    --add-data "version.txt:." \
    --collect-submodules PyQt6 \
    main.py

echo
echo "=========================================="
echo "  Build complete!"
echo "  Output: dist/CrossBible.app"
echo
echo "  실행:  open dist/CrossBible.app"
echo "  (서명 안 된 앱이라 처음엔 우클릭 → 열기, 또는"
echo "   시스템 설정 → 개인정보 보호 및 보안 → '확인 없이 열기' 필요할 수 있어요.)"
echo "=========================================="
