# 하드웨어 복구 계획서

방탈출 체험존 시스템 긴급 복구 가이드

## 목차

1. [시스템 개요](#시스템-개요)
2. [하드웨어 목록](#하드웨어-목록)
3. [네트워크 구성](#네트워크-구성)
4. [복구 우선순위](#복구-우선순위)
5. [장치별 복구 절차](#장치별-복구-절차)
6. [설정 파일 백업](#설정-파일-백업)
7. [테스트 절차](#테스트-절차)
8. [문제 해결](#문제-해결)

---

## 시스템 개요

```
┌─────────────────┐      MQTT       ┌─────────────────┐      USB       ┌─────────────┐
│  Home Assistant │◄───────────────►│  Raspberry Pi   │◄──────────────►│    ESP32    │
│  192.168.0.100   │                 │  192.168.0.28   │  /dev/ttyUSB0  │  Morse DAC  │
│  Mosquitto      │                 │  VLC + mpg123   │                │  GPIO 25/26 │
│  IKEA RODRET x2 │                 └─────────────────┘                └─────────────┘
└────────┬────────┘
         │ MQTT
         ▼
┌─────────────────────────────────────┐
│   Mac mini (192.168.0.24)           │
│   ├─ MP3 플레이어 (old_tv/mac.py)   │
│   ├─ tts_test/ (대본 TTS)           │
│   ├─ photo/ (카메라 모니터링)        │
│   ├─ photo_layout/ (6컷 인쇄)       │
│   └─ reserve/ (역재생 분석)          │
└─────────────────────────────────────┘
```

---

## 하드웨어 목록

### 필수 장비

| 장비 | 모델/사양 | 용도 | 구매처 |
|------|----------|------|--------|
| **Raspberry Pi** | Pi 4/5, 4GB+ | 영상/MP3/모스 플레이어 | 엘레파츠, 디바이스마트 |
| **ESP32** | CP2102N USB-UART | 오실로스코프 모스 출력 | 알리익스프레스, 엘레파츠 |
| **Home Assistant** | RPi 또는 PC | MQTT 브로커, 자동화 허브 | - |
| **Mac mini** | M1/M2 | macOS MP3 플레이어 | Apple |
| **Canon 100D** | EOS 100D (USB) | 사진 촬영 | 중고 |
| **DNP DS620** | 6x8" 포토 프린터 | 레이아웃 인쇄 | - |
| **IKEA RODRET** | ZHA 리모컨 x2 | 씬 제어 | IKEA |
| **오실로스코프** | X-Y 모드 지원 | 모스 부호 표시 | - |

### 케이블 및 연결

| 케이블 | 용도 |
|--------|------|
| HDMI | RPi → 모니터/TV (영상 출력) |
| 3.5mm 오디오 | RPi → 스피커 (MP3 출력) |
| USB-A to USB-C/Micro | ESP32 연결 |
| BNC 프로브 x2 | ESP32 DAC → 오실로스코프 |
| USB-A to Mini-B | Canon 100D 연결 |
| 이더넷 | 유선 네트워크 |

---

## 네트워크 구성

### IP 주소 할당

| 장치 | IP | MAC (예시) | 비고 |
|------|-----|------------|------|
| Home Assistant | 192.168.0.100 | - | DHCP 고정 또는 static |
| Raspberry Pi | 192.168.0.28 | - | eth0 고정 IP |
| Mac mini | 192.168.0.24 | - | DHCP 고정 |
| 공유기 | 192.168.0.1 | - | 기본 게이트웨이 |

### 공유기 설정 (DHCP 예약)

```
Home Assistant: 192.168.0.100
Raspberry Pi:   192.168.0.28
Mac mini:       192.168.0.24
```

### 방화벽 포트

| 포트 | 프로토콜 | 용도 |
|------|----------|------|
| 22 | TCP | SSH |
| 1883 | TCP | MQTT |
| 8123 | TCP | Home Assistant Web UI |

---

## 복구 우선순위

긴급 상황 시 아래 순서로 복구:

1. **🔴 Home Assistant** - 전체 시스템 제어의 핵심
2. **🔴 Raspberry Pi** - 영상/음향 출력
3. **🟡 Mac mini** - macOS MP3 플레이어 (대체 가능)
4. **🟡 ESP32** - 모스 부호 (부가 기능)
5. **🟢 Canon/DNP** - 사진 체험 (별도 운영 가능)

---

## 장치별 복구 절차

### 1. Home Assistant 복구

#### 1.1 신규 설치 (Raspberry Pi 기준)

```bash
# 1. Raspberry Pi Imager로 Home Assistant OS 설치
# https://www.home-assistant.io/installation/raspberrypi

# 2. 첫 부팅 후 http://homeassistant.local:8123 접속
# 3. 계정 생성: mystery / qwerqwer

# 4. SSH 애드온 설치
# Settings → Add-ons → SSH & Web Terminal → Install
```

#### 1.2 Mosquitto MQTT 브로커 설치

```bash
# Settings → Add-ons → Mosquitto broker → Install

# 설정 (Configuration 탭):
logins:
  - username: mystery
    password: qwerqwer
```

#### 1.3 ZHA 설정 (RODRET 리모컨)

```bash
# Settings → Devices & Services → Add Integration → ZHA
# Zigbee 동글 연결 필요 (예: ConBee II, SONOFF Zigbee)

# RODRET 페어링:
# 1. 리모컨 뒷면 페어링 버튼 5초 누름
# 2. ZHA에서 장치 추가
# 3. device_id 기록:
#    - RODRET 1 (씬0-3): 91afeecd96c2793ecdfebd81c5e5bc11
#    - RODRET 2 (씬4-5): 40d8a5e1c093a93e6206baf6d0e29fea
```

#### 1.4 input_number 헬퍼 생성

```yaml
# Settings → Devices & Services → Helpers → Create Helper → Number

# 또는 configuration.yaml:
input_number:
  scene_state:
    name: "현재 씬 번호"
    min: 0
    max: 5
    step: 1
    initial: 0
```

#### 1.5 자동화 복원

```bash
# 이 저장소의 ha/automations/old_tv.yaml 내용을
# /homeassistant/automations.yaml에 추가

# SSH로 접속:
sshpass -p 'qwerqwer' ssh mystery@192.168.0.100

# 파일 복사 (외부에서):
scp ha/automations/old_tv.yaml mystery@192.168.0.100:/homeassistant/

# HA에서 병합 또는 UI에서 직접 추가
```

#### 1.6 스위치 엔티티 확인

다음 엔티티가 존재해야 함 (스마트 플러그 등):
- `switch.doll`
- `switch.monkey`
- `switch.light1`
- `switch.light2`

---

### 2. Raspberry Pi 복구

#### 2.1 OS 설치

```bash
# Raspberry Pi Imager로 Raspberry Pi OS Lite (64-bit) 설치
# 사용자: pi / 비밀번호: 1

# SSH 활성화:
# Imager 설정에서 SSH 활성화 체크

# 고정 IP 설정 (/etc/dhcpcd.conf):
interface eth0
static ip_address=192.168.0.28/24
static routers=192.168.0.1
static domain_name_servers=8.8.8.8
```

#### 2.2 기본 패키지 설치

```bash
# SSH 접속
sshpass -p '1' ssh pi@192.168.0.28

# 패키지 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지
sudo apt install -y \
    python3-pip \
    vlc \
    mpg123 \
    screen \
    git

# Python 패키지
pip3 install paho-mqtt pyserial
```

#### 2.3 파일 배포

```bash
# 로컬에서 RPi로 복사
scp old_tv/mqtt_video_player.py pi@192.168.0.28:~/
scp old_tv/mqtt_mp3_morse_player.py pi@192.168.0.28:~/
scp old_tv/patterns.json pi@192.168.0.28:~/mp3/

# 미디어 폴더 생성
ssh pi@192.168.0.28 "mkdir -p ~/videos ~/mp3"

# 미디어 파일 복사 (영상, MP3)
scp videos/*.mp4 pi@192.168.0.28:~/videos/
scp mp3/*.mp3 pi@192.168.0.28:~/mp3/
```

#### 2.4 systemd 서비스 설정

**mqtt-video.service:**
```bash
sudo tee /etc/systemd/system/mqtt-video.service << 'EOF'
[Unit]
Description=MQTT Video Player
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/mqtt_video_player.py
Restart=always
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
EOF
```

**mqtt-mp3-morse.service:**
```bash
sudo tee /etc/systemd/system/mqtt-mp3-morse.service << 'EOF'
[Unit]
Description=MQTT MP3 + Morse Player
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/mqtt_mp3_morse_player.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

**volume-max.service (부팅 시 볼륨 100%):**
```bash
sudo tee /etc/systemd/system/volume-max.service << 'EOF'
[Unit]
Description=Set Volume to Maximum
After=sound.target

[Service]
Type=oneshot
ExecStart=/usr/bin/amixer set Master 100%
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
```

**서비스 활성화:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mqtt-video mqtt-mp3-morse volume-max
sudo systemctl start mqtt-video mqtt-mp3-morse volume-max
```

#### 2.5 오디오 설정

```bash
# HDMI와 3.5mm 동시 출력 설정
# /boot/config.txt에 추가:
dtparam=audio=on

# 또는 특정 출력 강제:
# HDMI: amixer cset numid=3 2
# 3.5mm: amixer cset numid=3 1
```

---

### 3. ESP32 복구

#### 3.1 펌웨어 업로드 준비

```bash
# Arduino IDE 설치 또는 PlatformIO

# ESP32 보드 매니저 URL 추가:
# https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

# 라이브러리 설치:
# - PubSubClient
# - ArduinoJson
```

#### 3.2 secrets.h 생성

```cpp
// old_tv/morse/secrets.h

#ifndef SECRETS_H
#define SECRETS_H

// WiFi 설정
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// MQTT 설정
#define MQTT_SERVER "192.168.0.100"
#define MQTT_PORT 1883
#define MQTT_USER "mystery"
#define MQTT_PASSWORD "qwerqwer"

// 장치 설정
#define DEVICE_NAME "morse_oscilloscope"
#define DEVICE_FRIENDLY_NAME "Morse Oscilloscope"

#endif
```

#### 3.3 펌웨어 업로드

```bash
# 1. ESP32를 USB로 연결
# 2. Arduino IDE에서 old_tv/morse/morse.ino 열기
# 3. 보드: ESP32 Dev Module
# 4. 포트: /dev/ttyUSB0 (또는 COM#)
# 5. 업로드 버튼 클릭
```

#### 3.4 오실로스코프 연결

```
ESP32 GPIO 26 (DAC2) → 오실로스코프 X축 (CH1)
ESP32 GPIO 25 (DAC1) → 오실로스코프 Y축 (CH2)
ESP32 GND           → 오실로스코프 GND

오실로스코프 설정:
- 모드: X-Y
- 시간축: 외부 또는 X-Y 모드
- 전압: 0~3.3V 범위
```

#### 3.5 시리얼 테스트

```bash
# RPi 또는 PC에서:
screen /dev/ttyUSB0 115200

# 명령어:
PATTERN:0   # 8 (---.. ) 출력
PATTERN:1   # X (-..- ) 출력
PATTERN:2   # 3 (...-- ) 출력
PATTERN:3   # U (..- ) 출력
STOP        # 화면 비움
STATUS      # 상태 확인
```

---

### 4. Mac mini 복구 (macOS MP3 플레이어)

#### 4.1 기본 설정

```bash
# Python3 확인 (macOS 기본 포함)
python3 --version

# pip 패키지 설치
pip3 install paho-mqtt
```

#### 4.2 mac.py 배포 및 실행

```bash
# 파일 복사
scp old_tv/mac.py kim@192.168.0.24:~/

# MP3 폴더 생성 및 파일 복사
ssh kim@192.168.0.24 "mkdir -p ~/mp3"
scp mp3/*.mp3 kim@192.168.0.24:~/mp3/

# 실행
ssh kim@192.168.0.24 "python3 ~/mac.py"
```

#### 4.3 자동 시작 (LaunchAgent)

```bash
# ~/Library/LaunchAgents/com.mystery.mp3player.plist
cat << 'EOF' > ~/Library/LaunchAgents/com.mystery.mp3player.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mystery.mp3player</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/kim/mac.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/kim</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# 서비스 로드
launchctl load ~/Library/LaunchAgents/com.mystery.mp3player.plist
```

---

### 5. macOS 앱 복구 (photo, photo_layout, reserve)

#### 5.1 photo (Canon 카메라 모니터링)

```bash
# 의존성 설치
brew install libgphoto2 pkg-config
pip3 install gphoto2 pillow requests

# 설정 파일 확인/수정
# photo/config.json에서 경로와 API 키 설정

# 실행
cd photo
./start.command
# 또는: python3 gui.py
```

**config.json 필수 설정:**
```json
{
  "paths": {
    "original_folder": "downloaded_photos",
    "overlay_image": "/path/to/overlay.png",
    "output_folder": "processed_photos"
  },
  "ai": {
    "api_key": "YOUR_GEMINI_API_KEY"
  }
}
```

#### 5.2 photo_layout (6컷 레이아웃 인쇄)

```bash
# 의존성
pip3 install pillow

# 실행
cd photo_layout
./start.command
# 또는: python3 gui.py
```

#### 5.3 reserve (역재생 오디오 분석기)

```bash
# 의존성
brew install ffmpeg
pip3 install PyQt5 numpy scipy pydub matplotlib pygame

# 실행
cd reserve
python3 qt_scope.py
```

#### 5.4 tts_test (대본 기반 TTS)

Mac mini에서 실행되는 펑션키 기반 대사 재생 시스템

```bash
# Python 3.12 필요 (tkinter 호환성)
# Mac mini에서는 /usr/local/bin/python3.12 사용

# 의존성 (macOS 기본 포함)
# tkinter, subprocess (say 명령어)

# 파일 배포
sshpass -p '1111' scp tts_test/main.py tts_test/scripts.json kim@192.168.0.24:~/

# 실행 (원격)
sshpass -p '1111' ssh kim@192.168.0.24 '/usr/local/bin/python3.12 ~/main.py'

# 또는 로컬 실행
cd tts_test && python3.12 main.py
```

**조작법:**
| 키 | 기능 |
|----|------|
| F1~F10 | 대본 재생 |
| 같은 키 재누름 | 즉시 중지 |
| ← / → | 이전/다음 문장 탐색 |
| Enter | 직접 입력 텍스트 재생 |
| ESC | 종료 |

**대본 수정:**
`scripts.json` 파일 직접 수정 (코드 수정 불필요)
```json
{
    "F1": "첫 번째 대사. 두 번째 문장.",
    "F2": "..."
}
```

**자동 시작 (LaunchAgent):**
```bash
cat << 'EOF' > ~/Library/LaunchAgents/com.mystery.tts.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mystery.tts</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3.12</string>
        <string>/Users/kim/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/kim</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.mystery.tts.plist
```

**원격 배포 + 재시작 (한 줄):**
```bash
sshpass -p '1111' scp tts_test/main.py tts_test/scripts.json kim@192.168.0.24:~/ && \
sshpass -p '1111' ssh kim@192.168.0.24 'pkill -f "python3.12 main.py"; osascript -e "tell application \"Terminal\" to do script \"cd ~ && /usr/local/bin/python3.12 main.py\""'
```

---

## 설정 파일 백업

### 백업 체크리스트

| 파일 | 위치 | 설명 |
|------|------|------|
| `automations.yaml` | HA: `/homeassistant/` | 씬 제어 자동화 |
| `configuration.yaml` | HA: `/homeassistant/` | HA 기본 설정 |
| `secrets.h` | `old_tv/morse/` | ESP32 WiFi/MQTT 인증 |
| `config.json` | `photo/` | 카메라/AI 설정 |
| `config.json` | `photo_layout/` | 레이아웃 설정 |
| `patterns.json` | `old_tv/` | 트랙별 패턴 매핑 |
| `scripts.json` | `tts_test/` | F1~F10 대본 내용 |
| `main.py` | `tts_test/` | TTS 프로그램 본체 |
| `*.mp3, *.mp4` | RPi: `~/videos/`, `~/mp3/` | 미디어 파일 |

### 백업 스크립트

```bash
#!/bin/bash
# backup.sh - 전체 설정 백업

BACKUP_DIR="backup_$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# HA 설정 (SSH 필요)
scp mystery@192.168.0.100:/homeassistant/automations.yaml $BACKUP_DIR/
scp mystery@192.168.0.100:/homeassistant/configuration.yaml $BACKUP_DIR/

# RPi 파일
scp pi@192.168.0.28:~/mqtt_video_player.py $BACKUP_DIR/
scp pi@192.168.0.28:~/mqtt_mp3_morse_player.py $BACKUP_DIR/
scp -r pi@192.168.0.28:~/mp3 $BACKUP_DIR/
scp -r pi@192.168.0.28:~/videos $BACKUP_DIR/

# 로컬 설정
cp photo/config.json $BACKUP_DIR/photo_config.json
cp photo_layout/config.json $BACKUP_DIR/photo_layout_config.json
cp old_tv/morse/secrets.h $BACKUP_DIR/

# tts_test 설정
cp tts_test/scripts.json $BACKUP_DIR/
cp tts_test/main.py $BACKUP_DIR/

# Mac mini에서 tts_test 백업 (원격)
scp kim@192.168.0.24:~/main.py $BACKUP_DIR/mac_mini_main.py
scp kim@192.168.0.24:~/scripts.json $BACKUP_DIR/mac_mini_scripts.json

echo "백업 완료: $BACKUP_DIR"
```

---

## 테스트 절차

### 1단계: 네트워크 연결 확인

```bash
# 각 장치 ping 테스트
ping -c 3 192.168.0.100  # Home Assistant
ping -c 3 192.168.0.28   # Raspberry Pi
ping -c 3 192.168.0.24   # Mac mini
```

### 2단계: MQTT 브로커 테스트

```bash
# mosquitto 클라이언트 설치 (macOS)
brew install mosquitto

# 구독 (터미널 1)
mosquitto_sub -h 192.168.0.100 -u mystery -P qwerqwer -t "#" -v

# 발행 (터미널 2)
mosquitto_pub -h 192.168.0.100 -u mystery -P qwerqwer -t "test" -m "hello"
```

### 3단계: 개별 기능 테스트

```bash
# 영상 재생 테스트
mosquitto_pub -h 192.168.0.100 -u mystery -P qwerqwer \
  -t "old_tv/video" -m "1.mp4"

# MP3 재생 테스트 (RPi)
mosquitto_pub -h 192.168.0.100 -u mystery -P qwerqwer \
  -t "mp3_morse/track" -m "morse.mp3"

# MP3 재생 테스트 (macOS)
mosquitto_pub -h 192.168.0.100 -u mystery -P qwerqwer \
  -t "macos_mp3/track" -m "1.mp3"

# ESP32 패턴 테스트
mosquitto_pub -h 192.168.0.100 -u mystery -P qwerqwer \
  -t "scene/esp32_pattern" -m "0"

# 정지
mosquitto_pub -h 192.168.0.100 -u mystery -P qwerqwer \
  -t "old_tv/command" -m "stop"
```

### 4단계: 씬 순차 테스트

1. Home Assistant UI에서 `input_number.scene_state` 확인
2. RODRET 끄기 버튼으로 0→1→2→3 순차 진행 확인
3. RODRET 켜기 버튼으로 씬 0 리셋 확인

### 5단계: 전체 시나리오 테스트

```
씬 0: 모든 장치 정지 확인
씬 1: morse.mp3 재생 + 오실로스코프 패턴 확인
씬 2: 1.mp4 영상 + 1.mp3 macOS 재생 + monkey ON 확인
씬 3: 2.mp4 단일재생 + 2.mp3 단일재생 + doll ON → 종료 시 OFF 확인
```

---

## 문제 해결

### MQTT 연결 실패

```bash
# 브로커 상태 확인 (HA)
# Settings → Add-ons → Mosquitto broker → Log

# 인증 정보 확인
# username: mystery
# password: qwerqwer

# 방화벽 확인
sudo ufw allow 1883/tcp
```

### RPi 서비스 오류

```bash
# 서비스 상태 확인
sudo systemctl status mqtt-video
sudo systemctl status mqtt-mp3-morse

# 로그 확인
journalctl -u mqtt-video -f
journalctl -u mqtt-mp3-morse -f

# 서비스 재시작
sudo systemctl restart mqtt-video
sudo systemctl restart mqtt-mp3-morse
```

### ESP32 시리얼 연결 실패

```bash
# 포트 확인
ls -la /dev/ttyUSB*
ls -la /dev/ttyACM*

# 권한 문제
sudo chmod 666 /dev/ttyUSB0
# 또는 사용자를 dialout 그룹에 추가
sudo usermod -a -G dialout pi

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

### VLC 영상 재생 안됨

```bash
# X 디스플레이 설정
export DISPLAY=:0

# VLC 테스트
cvlc --fullscreen --no-osd ~/videos/1.mp4

# 권한 문제
sudo usermod -a -G video pi
```

### Canon 카메라 연결 실패

```bash
# macOS에서 카메라 데몬 종료
killall PTPCamera 2>/dev/null
killall ptpcamerad 2>/dev/null

# gphoto2 테스트
gphoto2 --auto-detect
gphoto2 --summary
```

---

## 긴급 연락처 / 참고 자료

### 접속 정보 요약

```bash
# Home Assistant
sshpass -p 'qwerqwer' ssh mystery@192.168.0.100
# Web UI: http://192.168.0.100:8123

# Raspberry Pi
sshpass -p '1' ssh pi@192.168.0.28

# Mac mini
sshpass -p '1111' ssh kim@192.168.0.24
```

### 공식 문서

- [Home Assistant](https://www.home-assistant.io/docs/)
- [Mosquitto MQTT](https://mosquitto.org/documentation/)
- [ESP32 Arduino](https://docs.espressif.com/projects/arduino-esp32/)
- [gphoto2](http://gphoto.org/doc/)

---

## 버전 기록

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-01-27 | 1.0 | 초기 복구 계획서 작성 |
