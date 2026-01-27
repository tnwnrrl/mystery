#!/usr/bin/env python3
"""
macOS MQTT MP3 Player
- MQTT 토픽으로 MP3 재생 제어
- macos_mp3/track → 파일명 수신 시 재생
- macos_mp3/command → stop 수신 시 종료
"""

import paho.mqtt.client as mqtt
import subprocess
import os
import signal
import sys

# ========== 설정 ==========
MQTT_BROKER = "192.168.0.100"
MQTT_PORT = 1883
MQTT_USER = "mystery"
MQTT_PASSWORD = "qwerqwer"

# MP3 파일 경로 (나중에 설정)
MP3_DIR = "/Users/jjh/SynologyDrive/일산 신규 프로젝트/장치/old_TV/mp3"

# MQTT 토픽
TOPIC_TRACK = "macos_mp3/track"
TOPIC_COMMAND = "macos_mp3/command"
TOPIC_STATE = "macos_mp3/state"

# ========== 전역 변수 ==========
player_process = None

# ========== MP3 재생 ==========
def play_mp3(filename):
    global player_process

    # 기존 재생 중지
    stop_mp3()

    filepath = os.path.join(MP3_DIR, filename)
    if not os.path.exists(filepath):
        print(f"파일 없음: {filepath}")
        return False

    try:
        # macOS afplay 사용
        player_process = subprocess.Popen(
            ["afplay", filepath],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"재생 시작: {filename}")
        return True
    except Exception as e:
        print(f"재생 오류: {e}")
        return False

def stop_mp3():
    global player_process

    if player_process:
        try:
            player_process.terminate()
            player_process.wait(timeout=2)
        except:
            player_process.kill()
        player_process = None
        print("재생 중지")

# ========== MQTT 콜백 ==========
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"MQTT 연결됨: {MQTT_BROKER}")
        client.subscribe(TOPIC_TRACK)
        client.subscribe(TOPIC_COMMAND)
        client.publish(TOPIC_STATE, "stopped", retain=True)
    else:
        print(f"MQTT 연결 실패: {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode().strip()
    print(f"수신 [{topic}]: {payload}")

    if topic == TOPIC_TRACK:
        if payload:
            if play_mp3(payload):
                client.publish(TOPIC_STATE, "playing", retain=True)
            else:
                client.publish(TOPIC_STATE, "error", retain=True)

    elif topic == TOPIC_COMMAND:
        if payload.lower() == "stop":
            stop_mp3()
            client.publish(TOPIC_STATE, "stopped", retain=True)

# ========== 종료 처리 ==========
def signal_handler(sig, frame):
    print("\n종료 중...")
    stop_mp3()
    sys.exit(0)

# ========== 메인 ==========
def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # MP3 디렉토리 생성
    os.makedirs(MP3_DIR, exist_ok=True)
    print(f"MP3 디렉토리: {MP3_DIR}")

    # MQTT 클라이언트 설정
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        print("MQTT 연결 중...")
        client.loop_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"오류: {e}")
    finally:
        stop_mp3()
        client.disconnect()

if __name__ == "__main__":
    main()
