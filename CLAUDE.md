# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

라즈베리파이 + ESP32 + macOS 기반 Home Assistant 연동 멀티미디어 시스템
- **old_tv**: MQTT 제어 영상 재생 (HDMI)
- **mp3_morse**: MP3 재생 (3.5mm) + 오실로스코프 패턴 동기화
- **macos_mp3**: macOS MQTT MP3 플레이어 (afplay)
- **씬 제어**: IKEA RODRET 리모컨으로 씬 순차 진행

## Device Access

```bash
# Raspberry Pi SSH (유선)
sshpass -p '1' ssh pi@192.168.0.28

# Home Assistant SSH
sshpass -p 'qwerqwer' ssh mystery@192.168.0.25
```

## Architecture

```
┌─────────────────┐      MQTT       ┌─────────────────┐      USB       ┌─────────────┐
│  Home Assistant │◄───────────────►│  Raspberry Pi   │◄──────────────►│    ESP32    │
│  192.168.0.25   │                 │  192.168.0.28   │  /dev/ttyUSB0  │  Morse Code │
│                 │  old_tv/*       │                 │   Serial CMD   │  DAC25/26   │
│  Mosquitto      │  mp3_morse/*    │  ┌───────────┐  │                └─────────────┘
│                 │  scene/*        │  │ VLC(HDMI) │  │
│  IKEA RODRET    │                 │  │ mpg123    │  │
│  (ZHA 리모컨)    │  macos_mp3/*    │  │ (3.5mm)   │  │
└────────┬────────┘                 │  └───────────┘  │
         │                          └─────────────────┘
         │ MQTT
         ▼
┌─────────────────┐
│     macOS       │
│  afplay (MP3)   │
└─────────────────┘
```

## Network

| 장치 | 인터페이스 | IP | 용도 |
|------|-----------|-----|------|
| Raspberry Pi | eth0 | 192.168.0.28 | SSH 접속 |
| Raspberry Pi | wlan0 | 172.20.10.x | 인터넷 (iPhone) |
| Home Assistant | - | 192.168.0.25 | MQTT 브로커 |

## MQTT Topics

| 토픽 | 방향 | 값 |
|------|------|-----|
| `old_tv/command` | HA → RPi | play / stop |
| `old_tv/state` | RPi → HA | playing / stopped |
| `old_tv/video` | HA → RPi | 파일명 |
| `mp3_morse/command` | HA → RPi | play / stop |
| `mp3_morse/state` | RPi → HA | playing / stopped |
| `mp3_morse/track` | HA → RPi | MP3 파일명 |
| `macos_mp3/command` | HA → macOS | stop |
| `macos_mp3/track` | HA → macOS | MP3 파일명 |
| `macos_mp3/state` | macOS → HA | playing / stopped |
| `scene/esp32_pattern` | HA → RPi | 0-3 / STOP |

## ESP32 Serial Protocol

| 명령 | 설명 |
|------|------|
| `PATTERN:0` | 패턴 8 (---.. ) 출력 시작 |
| `PATTERN:1` | 패턴 X (-..- ) 출력 시작 |
| `PATTERN:2` | 패턴 3 (...-- ) 출력 시작 |
| `PATTERN:3` | 패턴 U (..- ) 출력 시작 |
| `STOP` | 출력 중지 (화면 비움) |
| `STATUS` | 현재 상태 조회 |

**동작**: 기본 대기(화면 비움) → PATTERN 명령 시 해당 기호 출력 → STOP 명령 시 대기

## Files

### Local (이 저장소)
| 파일 | 설명 |
|------|------|
| `morse.ino` | ESP32 오실로스코프 펌웨어 |
| `secrets.h` | WiFi/MQTT 인증정보 |
| `macos_mqtt_mp3_player.py` | macOS MQTT MP3 플레이어 |
| `mqtt_mp3_morse_player.py` | RPi MP3+Morse 플레이어 (백업) |

### Raspberry Pi
| 경로 | 설명 |
|------|------|
| `~/mqtt_video_player.py` | 영상 플레이어 (systemd: mqtt-video) |
| `~/mqtt_mp3_morse_player.py` | MP3+Morse 플레이어 (systemd: mqtt-mp3-morse) |
| `~/videos/` | 영상 파일 |
| `~/mp3/` | MP3 파일 |
| `~/mp3/patterns.json` | 트랙별 패턴 매핑 |

## Commands

```bash
# 서비스 상태
sudo systemctl status mqtt-video
sudo systemctl status mqtt-mp3-morse

# 로그 확인
journalctl -u mqtt-mp3-morse -f

# MQTT 테스트
mosquitto_pub -h 192.168.0.25 -u mystery -P qwerqwer -t "mp3_morse/track" -m "track1.mp3"
mosquitto_pub -h 192.168.0.25 -u mystery -P qwerqwer -t "mp3_morse/command" -m "stop"

# ESP32 시리얼 테스트
screen /dev/ttyUSB0 115200
# PATTERN:0 → OK:PATTERN:8 (8 출력 시작)
# STOP → OK:STOP (화면 비움)
```

## Pattern Mapping (patterns.json)

```json
{
  "track1.mp3": {
    "duration": 30,
    "patterns": [
      {"time": 0, "pattern": 0},
      {"time": 7.5, "pattern": 1},
      {"time": 15, "pattern": 2},
      {"time": 22.5, "pattern": 3}
    ]
  }
}
```

## Hardware

- **Raspberry Pi**: Linux 6.12.47 (aarch64)
- **ESP32**: CP2102N USB-UART, DAC GPIO 25/26
- **Display**: HDMI 1280x720 (VLC)
- **Audio**: 3.5mm (mpg123)
- **Remote**: IKEA RODRET (ZHA, device_id: 91afeecd96c2793ecdfebd81c5e5bc11)

## Scene Control (씬 순차 제어)

IKEA RODRET 리모컨으로 씬 순차 진행 (끄기 버튼) / 긴급 종료 (켜기 버튼)

| 씬 | 영상 | RPi MP3 | macOS MP3 | ESP32 | switch.doll |
|----|------|---------|-----------|-------|-------------|
| 0 | 정지 | 정지 | 정지 | STOP | OFF |
| 1 | - | morse.mp3 | - | 패턴 동기화 | - |
| 2 | 1.mp4 | - | - | 패턴0 | - |
| 3 | 2.mp4 | 정지 | 1.mp3 | 패턴1 | - |
| 4 | 3.mp4 | - | 2.mp3 | 패턴2 | ON |
| 5 | 정지 | - | 정지 | STOP | OFF |

**버튼 동작:**
- 끄기(off): 0→1→2→3→4→5→0 순차 진행
- 켜기(on): 씬0으로 즉시 리셋 (긴급 종료)

### Home Assistant 설정

```yaml
# input_number 헬퍼 (UI에서 생성 또는 configuration.yaml)
input_number:
  scene_state:
    name: "현재 씬 번호"
    min: 0
    max: 5
    step: 1
    initial: 0

# 자동화 파일: /homeassistant/automations.yaml
```

### Systemd Services (Raspberry Pi)

| 서비스 | 설명 |
|--------|------|
| `mqtt-video` | 영상 플레이어 |
| `mqtt-mp3-morse` | MP3+Morse 플레이어 |
| `volume-max` | 부팅 시 볼륨 100% 설정 |
