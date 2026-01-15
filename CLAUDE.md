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
| Home Assistant | - | 192.168.0.100 | MQTT 브로커 |
| Mac mini | - | 192.168.0.24 | macOS MP3 플레이어 |

## MQTT Topics

| 토픽 | 방향 | 값 |
|------|------|-----|
| `old_tv/command` | HA → RPi | play / stop |
| `old_tv/state` | RPi → HA | playing / stopped / finished |
| `old_tv/video` | HA → RPi | 파일명 (반복 재생) |
| `old_tv/video_once` | HA → RPi | 파일명 (단일 재생, 종료 시 finished) |
| `mp3_morse/command` | HA → RPi | play / stop |
| `mp3_morse/state` | RPi → HA | playing / stopped |
| `mp3_morse/track` | HA → RPi | MP3 파일명 |
| `macos_mp3/command` | HA → macOS | stop |
| `macos_mp3/track` | HA → macOS | MP3 파일명 (반복 재생) |
| `macos_mp3/track_once` | HA → macOS | MP3 파일명 (단일 재생) |
| `macos_mp3/state` | macOS → HA | playing / stopped / finished |
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

**자동 포트 감지**: mqtt_mp3_morse_player.py가 `/dev/ttyUSB*`, `/dev/ttyACM*` 스캔 후 ESP32 자동 연결. 연결 오류 시 자동 재연결

## Files

### Local (이 저장소)
| 파일 | 설명 |
|------|------|
| `morse/morse.ino` | ESP32 오실로스코프 펌웨어 |
| `morse/secrets.h` | WiFi/MQTT 인증정보 |
| `mac.py` | macOS MQTT MP3 플레이어 (반복/단일 재생 지원) |
| `mqtt_video_player.py` | RPi 영상 플레이어 (반복/단일 재생 + finished 이벤트) |
| `mqtt_mp3_morse_player.py` | RPi MP3+Morse 플레이어 |
| `ha_automations.yaml` | HA 씬 제어 자동화 (복사용) |
| `patterns.json` | 트랙별 패턴 매핑 |

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
mosquitto_pub -h 192.168.0.100 -u mystery -P qwerqwer -t "mp3_morse/track" -m "track1.mp3"
mosquitto_pub -h 192.168.0.100 -u mystery -P qwerqwer -t "mp3_morse/command" -m "stop"

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
- **Remote**: IKEA RODRET (ZHA, device_id: 91afeecd96c2793ecdfebd81c5e5bc11) - 씬0-3 제어
- **Remote2**: IKEA RODRET (ZHA, device_id: 40d8a5e1c093a93e6206baf6d0e29fea) - 씬4-5 제어

## Scene Control (씬 순차 제어)

### RODRET 리모컨 (씬 0-3)

| 씬 | 영상 | RPi MP3 | macOS MP3 | ESP32 | switch.doll | switch.monkey |
|----|------|---------|-----------|-------|-------------|---------------|
| 0 | 정지 | 정지 | 정지 | STOP | OFF | OFF |
| 1 | - | morse.mp3 | - | 패턴 동기화 | - | - |
| 2 | 1.mp4 | 정지 | 1.mp3 | STOP | - | ON |
| 3 | 2.mp4 (단일) | - | 2.mp3 (단일) | - | ON → MP3 종료 시 OFF | OFF |

**버튼 동작:**
- 끄기(off): 0→1→2→3 순차 진행 (3에서 멈춤)
- 켜기(on): 씬0으로 즉시 리셋 (긴급 종료)

### remote2 리모컨 (씬 4-5)

| 씬 | light1 | light2 | macOS MP3 |
|----|--------|--------|-----------|
| 4 | ON | ON | - |
| 5 | OFF → 3.mp3 종료 시 ON | OFF → 2초 후 ON | 3.mp3 (단일) |

**버튼 동작:**
- 끄기(off): 씬<4 → 씬4 (조명 켜기), 씬4 → 씬5 (시퀀스 실행)
- 켜기(on): 씬0으로 즉시 리셋

**씬5 시퀀스:**
light1,2 OFF → 1초 → 3.mp3 재생 → 2초 → light2 ON → 3.mp3 종료 → light1 ON

### Home Assistant 설정

**1. input_number 헬퍼 생성** (UI 또는 configuration.yaml):
```yaml
input_number:
  scene_state:
    name: "현재 씬 번호"
    min: 0
    max: 5
    step: 1
    initial: 0
```

**2. 자동화 추가** (ha_automations.yaml → /homeassistant/automations.yaml에 복사):
```bash
# HA SSH 접속 후
cat >> /homeassistant/automations.yaml < ha_automations.yaml
# 또는 HA UI에서 직접 추가
```

**3. RPi 플레이어 업데이트**:
```bash
# 영상 플레이어 (단일 재생 + finished 이벤트 지원)
scp mqtt_video_player.py pi@192.168.0.28:~/
sudo systemctl restart mqtt-video

# MP3+Morse 플레이어
scp mqtt_mp3_morse_player.py pi@192.168.0.28:~/
sudo systemctl restart mqtt-mp3-morse
```

**4. macOS 플레이어 업데이트** (Mac mini에서):
```bash
# mac.py를 Mac mini에 복사 후 실행
python3 mac.py
```

### Systemd Services (Raspberry Pi)

| 서비스 | 설명 |
|--------|------|
| `mqtt-video` | 영상 플레이어 |
| `mqtt-mp3-morse` | MP3+Morse 플레이어 |
| `volume-max` | 부팅 시 볼륨 100% 설정 |

## Troubleshooting

### ESP32 응답 없음
```bash
# 시리얼 포트 확인
ls -la /dev/ttyUSB*

# 직접 테스트
python3 -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=2)
ser.write(b'STATUS\n')
import time; time.sleep(0.3)
print(ser.readline())
ser.close()
"
```

### RPi 인터넷 연결
- eth0: 내부 네트워크 (192.168.0.x) - SSH 접속용
- wlan0: iPhone 핫스팟 연결 필요 (172.20.10.x) - 패키지 설치용
