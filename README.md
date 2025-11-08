# Canon 100D 사진 자동 처리 프로그램

Canon 100D 카메라에서 사진을 자동으로 가져와 PNG 레이어를 합성하는 Python 프로그램입니다.

## 주요 기능

✅ **실시간 모니터링** - 카메라에서 새 사진 자동 감지 및 다운로드
✅ **PNG 레이어 합성** - 투명도를 유지한 오버레이 자동 합성
✅ **GUI 인터페이스** - 직관적인 시작/종료 버튼과 실시간 로그
✅ **중복 방지** - 이미 처리된 파일 자동 추적
✅ **자동 크기 조정** - 모든 해상도 사진 지원

## 시스템 요구사항

- **OS**: macOS (현재 환경)
- **Python**: 3.7 이상
- **카메라**: Canon EOS 100D
- **연결**: USB 케이블

## 설치 방법

### 1. 시스템 의존성 설치

```bash
brew install libgphoto2 pkg-config
```

### 2. Python 가상환경 생성 (권장)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Python 패키지 설치

```bash
pip install -r requirements.txt
```

## 사용 방법

### GUI 모드 (권장)

```bash
python gui.py
```

**GUI 기능:**
- ▶ 모니터링 시작/종료 버튼
- 📊 실시간 처리 통계 (다운로드/합성/오류)
- 📝 실시간 로그 출력
- 🎛️ 5초 간격 자동 감지

**사용 단계:**
1. Canon 100D를 USB로 연결하고 전원 켜기
2. GUI에서 "▶ 모니터링 시작" 클릭
3. 카메라로 사진 촬영
4. 자동으로 다운로드 및 합성 진행
5. "⏹ 모니터링 종료"로 중단

### CLI 모드

**1회 실행 모드:**
```bash
python main.py
```
- 현재 카메라의 모든 새 파일 처리
- 완료 후 자동 종료

**실시간 모니터링 모드:**
```bash
python main.py --monitor
```
- 5초마다 카메라 확인
- Ctrl+C로 종료

## 프로젝트 구조

```
photo/
├── gui.py                  # GUI 프로그램 (메인 실행 파일)
├── main.py                 # CLI 모니터링 프로그램
├── config.json             # 설정 파일
├── requirements.txt        # Python 패키지 의존성
├── overlay.png             # PNG 오버레이 레이어 (1920x1080)
├── create_overlay.py       # 오버레이 생성 스크립트
│
├── utils/                  # 핵심 모듈
│   ├── camera.py           # Canon 카메라 연결 및 파일 관리
│   └── image_processor.py  # PNG 레이어 합성
│
├── downloaded_photos/      # 카메라에서 다운로드된 원본 사진
├── processed_photos/       # PNG 합성 완료 사진
└── processed_files.json    # 처리된 파일 추적 DB
```

## 설정 (config.json)

```json
{
  "camera": {
    "model": "Canon EOS 100D",
    "check_interval_seconds": 5
  },
  "paths": {
    "original_folder": "downloaded_photos",
    "overlay_image": "overlay.png",
    "output_folder": "processed_photos"
  },
  "processing": {
    "overlay_mode": "fullscreen",
    "preserve_original": true,
    "auto_process": true
  }
}
```

**설정 항목:**
- `check_interval_seconds`: 모니터링 감지 간격 (초)
- `overlay_image`: PNG 오버레이 파일 경로
- `original_folder`: 다운로드된 원본 저장 폴더
- `output_folder`: 합성된 사진 저장 폴더

## 오버레이 커스터마이징

### 기본 오버레이 (1920x1080)

- 상단/하단 반투명 테두리 (20px)
- 우하단 워터마크: "Canon 100D"

### 커스텀 오버레이 만들기

```bash
python create_overlay.py
```

`create_overlay.py`를 수정하여:
- 해상도 변경 (width, height)
- 테두리 두께 조정 (border_width)
- 폰트 크기 변경 (font size)
- 텍스트 내용 변경 (text)
- 색상 및 투명도 조정

## 문제 해결

### 카메라 연결 실패

```
❌ 카메라 연결 실패: [-53] Could not claim the USB device
```

**해결 방법:**
1. USB 케이블 확인
2. 카메라 전원 확인
3. macOS Photos 또는 Image Capture 앱 종료
4. 카메라 재연결

```bash
killall "Image Capture"
killall ptpcamerad
```

### gphoto2 모듈 임포트 실패

**해결 방법:**
```bash
brew install libgphoto2 pkg-config
pip install gphoto2
```

### 합성 결과가 이상함

- `overlay.png` 파일 확인
- 해상도가 1920x1080인지 확인
- `create_overlay.py`로 재생성

## 워크플로우

```
1. 카메라 촬영 (1920x1080 권장)
       ↓
2. USB 자동 감지
       ↓
3. 다운로드 → downloaded_photos/
       ↓
4. PNG 오버레이 합성
       ↓
5. 저장 → processed_photos/
       ↓
6. 처리 완료!
```

## 개발 정보

- **언어**: Python 3
- **주요 라이브러리**: gphoto2, Pillow, tkinter
- **버전**: 1.0.0
- **라이선스**: 개인 프로젝트

## 주의사항

- JPG/JPEG 파일만 지원 (RAW 미지원)
- USB 연결 필수 (WiFi 미지원)
- macOS 전용 (Windows/Linux 미테스트)
- 카메라 배터리 확인 (USB 장시간 연결)

## 참고사항

- 처리된 파일은 `processed_files.json`에 기록됩니다
- 원본 사진은 `downloaded_photos/`에 보존됩니다
- 합성 품질: JPEG 95% (고품질)
- 모니터링 중 카메라 조작 가능
