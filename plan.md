# Project Roadmap
> Created: 2026-01-07 | Last Updated: 2026-01-07

## Active Tasks
(없음)

## 최근 수정 (2026-01-08)
- [x] ESP32 시리얼 포트 수정: `/dev/ttyUSB1` → `/dev/ttyUSB0`
  - mqtt_mp3_morse_player.py 수정 완료
  - 서비스 재시작 완료

## 다음 단계
- [ ] ESP32에 morse.ino 펌웨어 업로드
- [ ] 테스트 MP3 파일 ~/mp3/에 업로드
- [ ] patterns.json 실제 트랙에 맞게 수정
- [ ] Home Assistant에 mp3_morse 엔티티 추가

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
