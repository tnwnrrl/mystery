#!/bin/bash
# Mac용 실행파일 빌드 스크립트

echo "🔨 Canon 100D 사진 처리 프로그램 빌드 시작 (Mac)"
echo "=================================================="

# 가상환경 활성화
source venv/bin/activate

# 기존 빌드 정리
echo "🧹 기존 빌드 파일 정리..."
rm -rf build dist

# PyInstaller로 빌드
echo "📦 실행파일 생성 중..."
pyinstaller build_mac.spec --clean

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 빌드 성공!"
    echo "=================================================="
    echo "📂 실행 파일 위치: dist/Canon100D.app"
    echo ""
    echo "사용 방법:"
    echo "1. dist/Canon100D.app을 Applications 폴더로 이동"
    echo "2. Canon100D.app을 더블클릭하여 실행"
    echo ""
    echo "⚠️  처음 실행 시:"
    echo "   - '확인되지 않은 개발자' 경고가 나올 수 있습니다"
    echo "   - 시스템 환경설정 > 보안 및 개인정보 보호에서"
    echo "   - '확인 없이 열기'를 클릭하세요"
else
    echo ""
    echo "❌ 빌드 실패"
    echo "오류 로그를 확인하세요"
    exit 1
fi
