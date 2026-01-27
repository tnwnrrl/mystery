#!/bin/bash
#
# ASA-2000 DMG 배포 파일 생성 스크립트
# 사용법: ./create_dmg.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="ASA-2000"
DMG_NAME="${APP_NAME}-1.0.0.dmg"
APP_PATH="dist/${APP_NAME}.app"
DMG_PATH="dist/${DMG_NAME}"

echo "=========================================="
echo "  ASA-2000 DMG 생성"
echo "=========================================="
echo ""

# 앱 번들 확인
if [ ! -d "$APP_PATH" ]; then
    echo "오류: ${APP_PATH}가 없습니다."
    echo "먼저 ./build.sh를 실행하세요."
    exit 1
fi

# 이전 DMG 삭제
rm -f "$DMG_PATH"

# 임시 디렉토리 생성
TMP_DIR=$(mktemp -d)
DMG_CONTENTS="${TMP_DIR}/dmg_contents"
mkdir -p "$DMG_CONTENTS"

echo "[1/3] 앱 복사 중..."
cp -R "$APP_PATH" "$DMG_CONTENTS/"

# Applications 폴더 링크 생성
echo "[2/3] Applications 링크 생성..."
ln -s /Applications "$DMG_CONTENTS/Applications"

# DMG 생성
echo "[3/3] DMG 생성 중..."
hdiutil create -volname "$APP_NAME" \
    -srcfolder "$DMG_CONTENTS" \
    -ov -format UDZO \
    "$DMG_PATH"

# 임시 파일 정리
rm -rf "$TMP_DIR"

echo ""
echo "=========================================="
echo "  DMG 생성 완료!"
echo "=========================================="
echo ""
echo "DMG 파일: $DMG_PATH"
echo ""
echo "배포 방법:"
echo "  1. DMG 파일을 다른 Mac에 복사"
echo "  2. DMG 더블클릭하여 마운트"
echo "  3. ASA-2000.app을 Applications 폴더로 드래그"
echo ""

# Finder에서 열기
open dist/
