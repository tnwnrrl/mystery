#!/bin/bash
# Canon 100D 자동 시작 스크립트 (카메라 연결 + GUI 실행)

cd "$(dirname "$0")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Canon 100D 사진 처리 시스템 자동 시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 카메라 프로세스 강제 종료
echo "🔧 1단계: 카메라 프로세스 정리..."
pkill -9 -f "ptpcamerad" 2>/dev/null
pkill -9 -f "mscamerad" 2>/dev/null
pkill -9 -f "icdd" 2>/dev/null
pkill -9 -f "cameracaptured" 2>/dev/null
killall -9 "Image Capture" 2>/dev/null
echo "   ✓ 프로세스 종료 완료"
sleep 1

# 2. 카메라 연결 시도 (최대 3회)
echo ""
echo "📸 2단계: 카메라 연결 시도..."

CONNECTED=false
MAX_ATTEMPTS=3

for attempt in $(seq 1 $MAX_ATTEMPTS); do
    echo "   시도 $attempt/$MAX_ATTEMPTS..."

    ./venv/bin/python -c "
import sys
sys.path.insert(0, '.')
from utils.camera import CameraConnection

try:
    camera = CameraConnection()
    if camera.connect():
        print('✅ 카메라 연결 성공!')
        print(f'   모델: {camera.camera_name}')
        camera.disconnect()
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f'   ❌ 실패: {e}')
    sys.exit(1)
" 2>&1

    if [ $? -eq 0 ]; then
        CONNECTED=true
        break
    fi

    # 재시도 전 프로세스 재정리 및 대기
    if [ $attempt -lt $MAX_ATTEMPTS ]; then
        pkill -9 -f "ptpcamerad" 2>/dev/null
        pkill -9 -f "mscamerad" 2>/dev/null
        sleep 2
    fi
done

# 3. 연결 결과에 따른 처리
if [ "$CONNECTED" = true ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✅ 카메라 연결 성공!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🚀 3단계: GUI 실행 중..."
    sleep 1

    # GUI 실행
    ./venv/bin/python gui.py

else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ❌ 카메라 연결 실패"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "💡 해결 방법:"
    echo "   1. USB 케이블을 뽑았다가 다시 연결"
    echo "   2. 5초 대기"
    echo "   3. 이 스크립트를 다시 실행"
    echo ""
    echo "또는"
    echo "   카메라 설정 → USB 모드 → Mass Storage로 변경"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi
