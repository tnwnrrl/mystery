# AUDIO SPECTRUM ANALYZER ASA-2000

오실로스코프 스타일의 오디오 역재생 분석기 (macOS, Python 3.11)

## 기능

- **오디오 파일 로드**: M4A, MP3, WAV 지원
- **역재생**: 오디오를 거꾸로 재생
- **속도 조절**: 0.5x ~ 2.0x 배속
- **파형 시각화**: 실시간 오디오 파형 표시
- **스펙트럼 분석기**: 주파수 스펙트럼 시각화
- **기술 정보 표시**: 샘플레이트, 비트레이트, 채널, 비트 깊이 등

## 설치

```bash
# ffmpeg 필요 (M4A, MP3 처리)
brew install ffmpeg

# 의존성 설치
pip install -r requirements.txt
```

## 실행

```bash
export QT_QPA_PLATFORM_PLUGIN_PATH="$(python -c 'import PyQt5; import os; print(os.path.dirname(PyQt5.__file__))')/Qt5/plugins/platforms"
python qt_scope.py
```

## 사용법

1. **FILE INPUT** → 오디오 파일 선택 (M4A/MP3/WAV)
2. **REVERSE** → 역재생 처리
3. **PLAY** → 재생
4. **SPEED** 슬라이더로 배속 조절
5. **PAUSE / STOP** → 일시정지 / 정지

## 요구사항

- Python 3.11+
- macOS
- ffmpeg
- PyQt5, pygame, numpy, pydub, matplotlib, pillow, scipy
