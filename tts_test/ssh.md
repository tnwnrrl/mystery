# SSH 접속 정보

일산 프로젝트 장치별 SSH 접속 정보

## 장치 목록

| 장치 | IP | 사용자 | 비밀번호 | 용도 |
|------|-----|--------|----------|------|
| Mac mini | 192.168.0.24 | kim | 1111 | TTS 자막, MP3 플레이어 |
| Raspberry Pi | 192.168.0.28 | pi | 1 | 영상 재생, Morse 제어 |
| Home Assistant | 192.168.0.100 | mystery | qwerqwer | MQTT 브로커, 자동화 |

## SSH 접속 명령어

```bash
# Mac mini
sshpass -p '1111' ssh kim@192.168.0.24

# Raspberry Pi
sshpass -p '1' ssh pi@192.168.0.28

# Home Assistant
sshpass -p 'qwerqwer' ssh mystery@192.168.0.100
```

## 파일 전송 (scp)

```bash
# Mac mini로 파일 전송
sshpass -p '1111' scp <파일> kim@192.168.0.24:~/

# Raspberry Pi로 파일 전송
sshpass -p '1' scp <파일> pi@192.168.0.28:~/

# Home Assistant로 파일 전송
sshpass -p 'qwerqwer' scp <파일> mystery@192.168.0.100:/homeassistant/
```

## 원격 명령 실행

```bash
# Mac mini에서 터미널 앱으로 스크립트 실행
sshpass -p '1111' ssh kim@192.168.0.24 'osascript -e "tell application \"Terminal\" to do script \"python3.12 main.py\""'

# Raspberry Pi에서 서비스 재시작
sshpass -p '1' ssh pi@192.168.0.28 'sudo systemctl restart mqtt-video'
```

## MQTT 브로커 정보

```
Host: 192.168.0.100
Port: 1883
User: mystery
Password: qwerqwer
```

## 참고

- sshpass 설치: `brew install hudochenkov/sshpass/sshpass`
- 네트워크: 192.168.0.x (내부망)
