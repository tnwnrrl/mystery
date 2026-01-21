#!/bin/bash
# 6컷 레이아웃 앱 실행 스크립트

cd "$(dirname "$0")"

echo "=========================================="
echo "  6컷 레이아웃 - DNP DS620"
echo "=========================================="

# Python 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되어 있지 않습니다."
    echo "   brew install python3"
    exit 1
fi

# Pillow 확인
if ! python3 -c "import PIL" 2>/dev/null; then
    echo "📦 Pillow 설치 중..."
    pip3 install Pillow>=9.0.0
fi

echo "🚀 앱 시작..."
python3 gui.py
