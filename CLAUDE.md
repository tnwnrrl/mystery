# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reverse Audio Analyzer - 오디오 역재생 및 분석 데스크톱 앱 (macOS, Python 3.11)

## Commands

```bash
# 설치
pip install -r requirements.txt

# 실행 (PyQt5 버전)
export QT_QPA_PLATFORM_PLUGIN_PATH="$(python -c 'import PyQt5; import os; print(os.path.dirname(PyQt5.__file__))')/Qt5/plugins/platforms"
python qt_scope.py
```

## Architecture

```
qt_scope.py (PyQt5 GUI)
    ↓
AudioProcessor (audio_processor.py)
    ↓
pydub (AudioSegment) + numpy (FFT)
```

### AudioProcessor 핵심 메서드

- `load_audio(file_path)` - M4A/MP3/WAV 로드
- `reverse_audio()` - 역재생 처리
- `change_speed(factor)` - 배속 조절 (0.5x ~ 2.0x)
- `get_audio_data()` - numpy 배열로 변환 (시각화용)
- `get_metadata()` - 샘플레이트, 비트레이트 등 메타데이터

## Notes

- pydub는 ffmpeg 필요 (M4A, MP3 처리)
- PyQt5 실행 시 QT_QPA_PLATFORM_PLUGIN_PATH 환경변수 필요
