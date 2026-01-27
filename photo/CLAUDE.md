# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Canon EOS 100D 카메라 모니터링 앱. USB로 사진 자동 다운로드 후 **하이브리드 처리**: AI 변환(Gemini) 우선, 오프라인 시 PNG 오버레이 폴백. tkinter GUI 제공.

## Commands

```bash
# 앱 실행 (권장)
./start.command

# 수동 GUI 실행
python3 gui.py

# 카메라 연결 테스트
python3 -c "
from utils.camera import CameraConnection
camera = CameraConnection()
print('✅ Connected' if camera.connect() else '❌ Failed')
camera.disconnect()
"

# AI 변환 테스트
python3 -c "
from utils.ai_transformer import check_internet, AITransformer
print('🌐 Internet:', '✅' if check_internet() else '❌')
"

# macOS 빌드
./build_mac.sh

# 의존성 설치
brew install libgphoto2 pkg-config
pip install -r requirements.txt
```

## Architecture

```
Camera (Canon 100D)
    ↓ USB (gphoto2)
CameraConnection.get_all_files()
    ↓
gui.py monitoring_loop()
    ↓ Download to downloaded_photos/
    ↓
┌─────────────────────────────────────────┐
│ HybridProcessor (하이브리드 모드)         │
├─────────────────────────────────────────┤
│ 1. 인터넷 연결 확인                       │
│ 2. AI 변환 시도 (AITransformer)          │
│    └─ 실패 시 → 오버레이 폴백             │
│ 3. 오버레이 합성 (ImageProcessor)        │
└─────────────────────────────────────────┘
    ↓
Save to processed_photos/
```

### Core Files

| 파일 | 역할 |
|------|------|
| `gui.py` | 메인 진입점. tkinter GUI (탭: 메인/AI설정/폴더) |
| `utils/camera.py` | `CameraConnection` - gphoto2 래퍼 |
| `utils/ai_transformer.py` | `AITransformer`, `HybridProcessor` - AI 변환 + 폴백 |
| `utils/image_processor.py` | `ImageProcessor` - Pillow RGBA 오버레이 |
| `config.json` | 설정 (API 키, 프롬프트, 모드, 경로) |
| `processed_files.json` | 처리 완료 파일 추적 |

## Processing Modes

| 모드 | 설명 | 사용 시점 |
|------|------|----------|
| `hybrid` | AI 우선, 실패 시 오버레이 폴백 | **기본값 (권장)** |
| `ai` | AI 전용 (오프라인 시 처리 안됨) | 항상 인터넷 가능할 때 |
| `overlay` | 오버레이 전용 | 오프라인 환경 |

## macOS Camera Connection Issue

**문제**: macOS 데몬(`ptpcamerad`, `mscamerad-xpc`, `icdd`)이 USB 카메라 자동 점유

**에러**: `[-53] Could not claim the USB device`

**해결**: `start.command`가 `pkill -9`로 프로세스 강제 종료 후 3회 재시도. 실패 시 USB 케이블 물리적 재연결.

## AI 변환 (Gemini)

**모델**: `gemini-2.5-flash-preview-05-20`

**비용**: ~$0.039/장 (약 50원), 무료 티어 ~1,500장/일

**처리 시간**: ~10초/장

**핵심**: 프롬프트에 "원본 얼굴, 옷, 포즈는 절대 바꾸지 마" 필수

```python
# API 사용 예
from utils.ai_transformer import AITransformer

config = {
    'api_key': 'AIzaSy...',
    'model': 'gemini-2.5-flash-preview-05-20',
    'prompt': '심령사진으로 변환...'
}
transformer = AITransformer(config)
success, msg = transformer.transform_image('input.jpg', 'output.jpg')
```

## Key Constraints

- **macOS only**: gphoto2가 Windows 미지원
- **JPG only**: RAW 파일 미지원
- **오버레이 RGBA 필수**: RGB 모드는 투명도 무시
- **카메라 연결 유지**: 모니터링 중 단일 연결 유지
- **인터넷 불안정 대응**: 하이브리드 모드로 오프라인 폴백 지원
