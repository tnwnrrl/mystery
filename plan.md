# Project Roadmap
> Created: 2026-01-07 | Last Updated: 2026-01-12

## Active Tasks

### MP3 파일 확인 (서버 연결 후 수행)

```bash
# Mac mini에서 MP3 파일 확인
sshpass -p '1111' ssh kim@192.168.0.24 "ls -la ~/Music/ha_mp3/"

# Mac mini에서 모든 MP3 파일 검색
sshpass -p '1111' ssh kim@192.168.0.24 "find ~ -name '*.mp3' 2>/dev/null"
```

**필요한 MP3 파일:**
| 파일 | 위치 | 용도 | 상태 |
|------|------|------|------|
| morse.mp3 | RPi ~/mp3/ | 씬1 - 패턴 동기화 | ✅ 확인됨 |
| 1.mp3 | Mac mini ~/Music/ha_mp3/ | 씬2 - 반복 재생 | ❓ 확인 필요 |
| 2.mp3 | Mac mini ~/Music/ha_mp3/ | 씬3 - 단일 재생 | ❓ 확인 필요 |

### 배포 작업 (서버 연결 후 수행)

1. **RPi 영상 플레이어 배포**
```bash
scp mqtt_video_player.py pi@192.168.0.28:~/
sshpass -p '1' ssh pi@192.168.0.28 "sudo systemctl restart mqtt-video"
```

2. **Mac mini 플레이어 배포**
```bash
scp mac.py kim@192.168.0.24:~/
sshpass -p '1111' ssh kim@192.168.0.24 "nohup python3 ~/mac.py > ~/mac.log 2>&1 &"
```

3. **HA 설정**
   - input_number.scene_state max를 3으로 변경
   - ha_automations.yaml 자동화 추가

## 최근 수정 (2026-01-08)
- [x] ESP32 시리얼 포트 자동 감지 기능 추가
  - `find_esp32_port()`: USB 포트 스캔 후 ESP32 자동 발견
  - `reconnect_serial()`: 연결 오류 시 자동 재연결
  - 스캔 범위: `/dev/ttyUSB*`, `/dev/ttyACM*`
  - systemd에 `PYTHONUNBUFFERED=1` 추가 (로그 즉시 출력)

## 다음 단계
- [x] ESP32에 morse.ino 펌웨어 업로드 → 이미 동작 중
- [x] 테스트 MP3 파일 ~/mp3/에 업로드 → morse.mp3 존재
- [x] patterns.json 실제 트랙에 맞게 수정 → 4개 패턴 설정됨
- [x] Home Assistant에 mp3_morse 엔티티 추가 → automations.yaml에 설정됨

## Completed Archive
- [x] 라즈베리파이 네트워크 재구성 (2026-01-07)
  - eth0 (유선): 192.168.0.28 - 인터넷
  - wlan0 (WiFi): 172.20.10.2 - iPhone 핫스팟
- [x] 라즈베리파이 SSH 접속 확인 (2026-01-07)
  - SSH 연결 성공 (pi@192.168.0.29)
  - mqtt-video 서비스 정상 동작 확인

## Learning Log
| Task | Issue | Retries | Resolution |
|------|-------|---------|------------|
