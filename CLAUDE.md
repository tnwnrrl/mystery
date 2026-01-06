# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

라즈베리파이 기반 MQTT 영상 재생 시스템 (old_TV) - Home Assistant 연동

## Device Access

```bash
# Raspberry Pi SSH
sshpass -p '1' ssh pi@192.168.0.29

# Home Assistant SSH
sshpass -p 'qwerqwer' ssh mystery@192.168.0.25

# 파일 업로드 (라즈베리파이)
sshpass -p '1' scp <local_file> pi@192.168.0.29:~/videos/
```

## Architecture

```
┌─────────────────┐      MQTT       ┌─────────────────┐
│  Home Assistant │◄───────────────►│  Raspberry Pi   │
│  192.168.0.25   │                 │  192.168.0.29   │
│                 │  old_tv/command │                 │
│  Mosquitto      │  old_tv/state   │  mqtt_video_    │
│  switch.old_tv  │  old_tv/video   │  player.py      │
└─────────────────┘                 └─────────────────┘
```

## Remote Scripts (Raspberry Pi)

| 경로 | 설명 |
|------|------|
| `~/mqtt_video_player.py` | MQTT 제어 영상 플레이어 (systemd 서비스) |
| `~/play_video.py` | VLC 기반 전체화면 반복 재생 (수동 실행용) |
| `~/videos/` | 영상 파일 저장 폴더 |

## MQTT Topics

| 토픽 | 방향 | 값 |
|------|------|-----|
| `old_tv/command` | HA → RPi | play / stop / status |
| `old_tv/state` | RPi → HA | playing / stopped |
| `old_tv/video` | HA → RPi | 파일명 (예: 2.mp4) |

## Commands

```bash
# 서비스 상태 확인 (라즈베리파이)
sudo systemctl status mqtt-video

# 서비스 재시작
sudo systemctl restart mqtt-video

# 로그 확인
journalctl -u mqtt-video -f

# MQTT 테스트 (재생)
mosquitto_pub -h 192.168.0.25 -u mystery -P qwerqwer -t "old_tv/command" -m "play"
```

## Hardware Specs

- **Raspberry Pi**: Linux 6.12.47 (aarch64), Python 3.13.5
- **Display**: 1280x720 (HD)
- **Network**: WiFi (mystery) 192.168.0.29
- **Video Player**: VLC
