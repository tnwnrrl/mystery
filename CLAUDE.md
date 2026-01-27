# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

방탈출 체험존 통합 시스템 - 5개 모듈의 모노레포

| 모듈 | 설명 | 플랫폼 |
|------|------|--------|
| `old_tv/` | RPi + ESP32 MQTT 멀티미디어 (영상/MP3/모스) | RPi, macOS |
| `photo/` | Canon 100D 카메라 모니터링 + AI 변환 | macOS |
| `photo_layout/` | DNP DS620 6컷 레이아웃 인쇄 | macOS |
| `reserve/` | Reverse Audio Analyzer (역재생 분석) | macOS |
| `tts_test/` | 대본 기반 TTS (F키 대사 재생) | macOS |

## Device Access

```bash
# Raspberry Pi SSH (유선)
sshpass -p '1' ssh pi@192.168.0.28

# Home Assistant SSH
sshpass -p 'qwerqwer' ssh mystery@192.168.0.100

# Mac mini SSH
sshpass -p '1111' ssh kim@192.168.0.24
```

## Architecture

```
┌─────────────────┐      MQTT       ┌─────────────────┐      USB       ┌─────────────┐
│  Home Assistant │◄───────────────►│  Raspberry Pi   │◄──────────────►│    ESP32    │
│  192.168.0.100   │                 │  192.168.0.28   │  /dev/ttyUSB0  │  Morse Code │
│                 │  old_tv/*       │                 │   Serial CMD   │  DAC25/26   │
│  Mosquitto      │  mp3_morse/*    │  ┌───────────┐  │                └─────────────┘
│                 │  scene/*        │  │ VLC(HDMI) │  │
│  IKEA RODRET    │                 │  │ mpg123    │  │
│  (ZHA 리모컨)    │  macos_mp3/*    │  │ (3.5mm)   │  │
└────────┬────────┘                 │  └───────────┘  │
         │                          └─────────────────┘
         │ MQTT
         ▼
┌─────────────────┐                 ┌─────────────────┐
│   Mac mini      │                 │    macOS        │
│   afplay (MP3)  │                 │  photo/         │
│   old_tv/mac.py │                 │  photo_layout/  │
│   tts_test/     │                 │  reserve/       │
└─────────────────┘                 └─────────────────┘
```

## Network

| 장치 | IP | 용도 |
|------|-----|------|
| Raspberry Pi (eth0) | 192.168.0.28 | old_tv 미디어 플레이어 |
| Home Assistant | 192.168.0.100 | MQTT 브로커, 자동화 |
| Mac mini | 192.168.0.24 | macOS MP3 플레이어 |

## MQTT Topics

### old_tv (영상/MP3)
| 토픽 | 방향 | 값 |
|------|------|-----|
| `old_tv/command` | HA → RPi | play / stop |
| `old_tv/video` | HA → RPi | 파일명 (반복 재생) |
| `old_tv/video_once` | HA → RPi | 파일명 (단일 재생) |
| `old_tv/state` | RPi → HA | playing / stopped / finished |
| `mp3_morse/command` | HA → RPi | play / stop |
| `mp3_morse/track` | HA → RPi | MP3 파일명 |
| `mp3_morse/state` | RPi → HA | playing / stopped |
| `macos_mp3/track` | HA → macOS | MP3 파일명 (반복) |
| `macos_mp3/track_once` | HA → macOS | MP3 파일명 (단일) |
| `macos_mp3/state` | macOS → HA | playing / stopped / finished |
| `scene/esp32_pattern` | HA → RPi | 0-3 / STOP |

## Module Details

### old_tv/
RPi + ESP32 + macOS 기반 Home Assistant 연동 멀티미디어 시스템
- **영상 재생**: VLC (HDMI)
- **MP3 재생**: mpg123 (3.5mm), afplay (macOS)
- **모스 부호**: ESP32 DAC → 오실로스코프
- **씬 제어**: IKEA RODRET 리모컨

```bash
# RPi 서비스 상태
sudo systemctl status mqtt-video mqtt-mp3-morse

# MQTT 테스트
mosquitto_pub -h 192.168.0.100 -u mystery -P qwerqwer -t "old_tv/video" -m "1.mp4"
```

### photo/
Canon EOS 100D 카메라 모니터링 앱
- USB gphoto2 연결
- 하이브리드 처리: AI 변환(Gemini) 우선, 오프라인 시 PNG 오버레이 폴백
- tkinter GUI

```bash
cd photo && ./start.command
```

### photo_layout/
DNP DS620 6컷 레이아웃 앱
- 6x8" 용지에 2x3 그리드 (1800x2400px)
- fill/fit 모드 지원
- macOS Preview 연동 인쇄

```bash
cd photo_layout && ./start.command
```

### reserve/
Reverse Audio Analyzer
- M4A/MP3/WAV 역재생
- 배속 조절 (0.5x ~ 2.0x)
- PyQt5 GUI + FFT 시각화

```bash
cd reserve && python qt_scope.py
```

### tts_test/
대본 기반 TTS 프로그램
- F1~F10 펑션키로 대사 재생
- 보조 모니터 자동 감지 및 전체화면
- macOS `say` 명령어 + Yuna 음성
- scripts.json으로 대본 관리

```bash
cd tts_test && python3.12 main.py

# Mac mini 원격 배포
sshpass -p '1111' scp tts_test/main.py tts_test/scripts.json kim@192.168.0.24:~/
```

## Home Assistant

자동화 설정은 `ha/automations/` 디렉토리에 있습니다.

```bash
# HA에 자동화 복사
scp ha/automations/old_tv.yaml mystery@192.168.0.100:/homeassistant/automations.yaml
```

## Hardware

| 장비 | 용도 |
|------|------|
| Raspberry Pi | 영상/MP3/모스 플레이어 |
| ESP32 (CP2102N) | 오실로스코프 모스 출력 (DAC 25/26) |
| Canon 100D | 사진 촬영 (gphoto2) |
| DNP DS620 | 6x8" 레이아웃 인쇄 |
| IKEA RODRET x2 | ZHA 리모컨 (씬 0-5 제어) |

## Quick Start

```bash
# 의존성 설치
pip install -r requirements.txt

# macOS 전용 (photo)
brew install libgphoto2 pkg-config

# reserve 전용 (ffmpeg)
brew install ffmpeg
```
