# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reverse Audio Analyzer - 오디오 역재생 및 분석 데스크톱 앱 (macOS, Python 3.11.9)

## Commands

```bash
# 설치
pip install -r requirements.txt

# 실행 (메인 버전 - macOS afplay 사용)
python main.py

# PyQt5 버전 실행
python qt_scope.py
```

## Architecture

```
AudioProcessor (audio_processor.py)
       ↑
       │ 모든 UI가 이 모듈을 import
       │
┌──────┴──────────────────────────────────┐
│  UI 변형들 (동일 기능, 다른 프레임워크)    │
├─────────────────────────────────────────┤
│ main.py            - tkinter + afplay   │ ← macOS 전용
│ qt_scope.py        - PyQt5 + pygame     │ ← 크로스플랫폼
│ main_enhanced.py   - tkinter + pygame   │
│ oscilloscope_player.py - tkinter + pygame │
│ scope_ui.py        - CustomTkinter      │
└─────────────────────────────────────────┘
```

### AudioProcessor 핵심 메서드

- `load_audio(file_path)` - MP3/WAV 로드
- `reverse_audio()` - 역재생 처리
- `change_speed(factor)` - 배속 조절 (0.5x ~ 2.0x)
- `get_audio_data()` - numpy 배열로 변환 (시각화용)
- `get_metadata()` - 샘플레이트, 비트레이트 등 메타데이터

### UI 버전 선택 기준

| 버전 | 오디오 재생 | 특징 |
|------|------------|------|
| `main.py` | afplay (macOS 네이티브) | 의존성 적음, macOS 전용 |
| `qt_scope.py` | pygame | PyQt5 필요, 크로스플랫폼 |

## Notes

- pydub는 ffmpeg 필요 (MP3 처리)
- Python 3.13+에서는 `audioop-lts` 추가 설치 필요
