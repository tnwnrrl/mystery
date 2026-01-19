#!/bin/bash
#
# ASA-2000 macOS 앱 빌드 스크립트
# 한글 경로 문제를 피하기 위해 임시 영문 경로에서 빌드
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  ASA-2000 macOS App Builder"
echo "=========================================="
echo ""

# 임시 빌드 디렉토리 (영문 경로)
BUILD_TMP="/tmp/asa2000_build"

# 1. 이전 임시 디렉토리 정리
echo "[1/6] 임시 빌드 디렉토리 준비..."
rm -rf "$BUILD_TMP"
mkdir -p "$BUILD_TMP"

# 2. 소스 파일 복사 (venv 제외)
echo "[2/6] 소스 파일 복사..."
cp qt_scope.py "$BUILD_TMP/"
cp audio_processor.py "$BUILD_TMP/"
cp config.py "$BUILD_TMP/"
cp visualization.py "$BUILD_TMP/"
cp requirements.txt "$BUILD_TMP/"
cp ASA-2000.spec "$BUILD_TMP/"

# 아이콘 복사 (있으면)
if [ -f "AppIcon.icns" ]; then
    cp AppIcon.icns "$BUILD_TMP/"
fi
if [ -f "AppIcon.png" ]; then
    cp AppIcon.png "$BUILD_TMP/"
fi

# scripts 폴더 복사
if [ -d "scripts" ]; then
    cp -r scripts "$BUILD_TMP/"
fi

cd "$BUILD_TMP"

# 3. 가상환경 생성 (Python 3.11 사용 - audioop 지원)
echo "[3/6] 가상환경 생성 (Python 3.11)..."
python3.11 -m venv venv
source venv/bin/activate

# 4. 의존성 설치
echo "[4/6] 의존성 설치..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet pyinstaller

# 5. 아이콘 생성 (없으면)
echo "[5/6] 앱 아이콘 확인..."
if [ ! -f "AppIcon.icns" ]; then
    if [ -f "scripts/create_icon.py" ]; then
        echo "      아이콘 생성 중..."
        python scripts/create_icon.py
    else
        echo "      경고: 아이콘 파일이 없습니다"
    fi
fi

# 6. PyInstaller로 앱 번들 생성
echo "[6/6] 앱 번들 생성 중 (시간이 걸릴 수 있습니다)..."
pyinstaller ASA-2000.spec --noconfirm

# 결과물을 원래 프로젝트로 복사
echo ""
echo "결과물 복사 중..."
rm -rf "$SCRIPT_DIR/dist"
rm -rf "$SCRIPT_DIR/build"
cp -R dist "$SCRIPT_DIR/"

# 임시 디렉토리 정리 (선택)
# rm -rf "$BUILD_TMP"

echo ""
echo "=========================================="
echo "  빌드 완료!"
echo "=========================================="
echo ""
echo "앱 위치: $SCRIPT_DIR/dist/ASA-2000.app"
echo ""
echo "실행 방법:"
echo "  1. Finder에서 dist/ASA-2000.app 더블클릭"
echo "  2. 또는: open dist/ASA-2000.app"
echo ""
echo "다른 Mac에 배포:"
echo "  1. dist/ASA-2000.app 폴더를 복사"
echo "  2. DMG 생성: ./create_dmg.sh (선택사항)"
echo ""

# Finder에서 열기
open "$SCRIPT_DIR/dist/"
