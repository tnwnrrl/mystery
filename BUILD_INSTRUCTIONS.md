# Canon 100D 실행파일 빌드 가이드

## Mac용 실행파일 빌드

### 요구사항
- macOS 10.13 이상
- Python 3.7 이상
- 모든 의존성 패키지 설치 완료

### 빌드 방법

```bash
# 실행 권한 부여
chmod +x build_mac.sh

# 빌드 실행
./build_mac.sh
```

### 빌드 결과
- **위치**: `dist/Canon100D.app`
- **크기**: 약 50-100MB
- **사용 방법**:
  1. `Canon100D.app`을 Applications 폴더로 이동
  2. 더블클릭하여 실행

### 첫 실행 시 보안 경고
macOS는 인증되지 않은 앱에 대해 경고를 표시합니다:

1. **경고 메시지**: "확인되지 않은 개발자"
2. **해결 방법**:
   - 시스템 환경설정 → 보안 및 개인정보 보호
   - 하단의 "확인 없이 열기" 클릭
   - 또는 앱을 우클릭 → "열기" 선택

---

## Windows용 실행파일 빌드

### 요구사항
- Windows 10/11
- Python 3.7 이상
- libgphoto2 Windows 버전 설치
- 모든 의존성 패키지 설치 완료

### 사전 준비

#### 1. Python 및 필수 패키지 설치
```cmd
python --version  # Python 3.7 이상 확인

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate.bat

# 패키지 설치
pip install -r requirements.txt
pip install pyinstaller
```

#### 2. libgphoto2 Windows 버전 설치
Windows에서는 libgphoto2 대신 다른 방법을 사용해야 할 수 있습니다:

**옵션 1**: WIA (Windows Image Acquisition) 사용
**옵션 2**: Canon SDK 사용
**옵션 3**: USB 드라이버를 통한 직접 접근

**⚠️ 주의**: Windows에서 gphoto2는 공식적으로 지원되지 않습니다.
카메라 연결 부분을 Windows API로 변경해야 할 수 있습니다.

### 빌드 방법 (gphoto2 대체 후)

```cmd
# 빌드 실행
build_windows.bat
```

### 빌드 결과
- **위치**: `dist\Canon100D.exe`
- **크기**: 약 30-80MB
- **사용 방법**:
  1. `Canon100D.exe`를 원하는 위치로 복사
  2. 더블클릭하여 실행

---

## Windows 호환성 해결 방안

### 방법 1: WIA 라이브러리 사용
```python
# utils/camera_windows.py 생성
import win32com.client

class CameraConnectionWin:
    def __init__(self):
        self.device_manager = win32com.client.Dispatch("WIA.DeviceManager")
    # ... WIA를 사용한 카메라 연결 구현
```

### 방법 2: Canon SDK 사용
- Canon EDSDK (EOS Digital Software Development Kit) 다운로드
- SDK를 사용한 카메라 연결 구현

### 방법 3: PyUSB 사용
```python
# 직접 USB 통신으로 카메라 제어
import usb.core
import usb.util
# ... USB 직접 통신 구현
```

---

## 배포 패키지 구성

### Mac 배포
```
Canon100D_Mac.zip
├── Canon100D.app
├── README_Mac.txt
└── overlay.png (샘플)
```

### Windows 배포
```
Canon100D_Windows.zip
├── Canon100D.exe
├── README_Windows.txt
├── overlay.png (샘플)
└── dependencies/
    └── (필요한 DLL 파일들)
```

---

## 트러블슈팅

### Mac: "손상되어 열 수 없습니다" 오류
```bash
# 격리 속성 제거
xattr -cr /Applications/Canon100D.app
```

### Mac: libgphoto2 라이브러리 누락
```bash
# Homebrew로 재설치
brew reinstall libgphoto2
```

### Windows: DLL 누락 오류
- Visual C++ Redistributable 설치
- 필요한 DLL을 exe와 같은 폴더에 복사

---

## 개발자 서명 (선택사항)

### Mac 코드 서명
```bash
# Apple Developer 인증서로 서명
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" Canon100D.app

# 공증 (Notarization)
xcrun notarytool submit Canon100D.app --apple-id "your@email.com" --wait
```

### Windows 코드 서명
```cmd
# DigiCert 등의 인증서로 서명
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com Canon100D.exe
```

---

## 빌드 문제 해결

### PyInstaller 오류 시
```bash
# 캐시 정리
pyinstaller --clean build_mac.spec

# 디버그 모드로 빌드
pyinstaller --debug=all build_mac.spec
```

### 모듈 누락 오류
```python
# build_mac.spec 또는 build_windows.spec에 추가
hiddenimports=['missing_module_name']
```

---

## 자동 업데이트 (고급)

향후 자동 업데이트 기능 추가 시:
- Sparkle (Mac)
- WinSparkle (Windows)
- 자체 업데이트 서버 구축

---

## 라이선스 및 배포

- 배포 시 Python 라이선스 명시 필요
- gphoto2 라이선스 (LGPL) 명시 필요
- Pillow 라이선스 명시 필요

---

**문의**: 빌드 관련 문제 발생 시 GitHub Issues 참조
