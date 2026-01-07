#!/usr/bin/env python3
"""
MQTT MP3 + Morse 동기화 플레이어 v2
- MP3 재생: mpg123 --remote 모드로 실제 재생 위치 추적
- 오실로스코프: 시리얼로 ESP32 패턴 동기화 (밀림 없음)
"""

import paho.mqtt.client as mqtt
import subprocess
import serial
import threading
import json
import time
import os
import signal
import sys
import re

# ========== 설정 ==========
MQTT_BROKER = "192.168.0.25"
MQTT_PORT = 1883
MQTT_USER = "mystery"
MQTT_PASSWORD = "qwerqwer"

SERIAL_PORT = "/dev/ttyUSB1"
SERIAL_BAUD = 115200

MP3_DIR = "/home/pi/mp3"
PATTERNS_FILE = "/home/pi/mp3/patterns.json"

# MQTT 토픽
TOPIC_COMMAND = "mp3_morse/command"
TOPIC_STATE = "mp3_morse/state"
TOPIC_TRACK = "mp3_morse/track"

# ========== 전역 변수 ==========
player_process = None
monitor_thread = None
playing = False
current_track = ""
serial_conn = None
current_patterns = []
current_pattern_idx = 0
track_duration = 0

# ========== 패턴 로드 ==========
def load_patterns():
    if os.path.exists(PATTERNS_FILE):
        with open(PATTERNS_FILE, 'r') as f:
            return json.load(f)
    return {}

# ========== 시리얼 통신 ==========
def init_serial():
    global serial_conn
    try:
        serial_conn = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        time.sleep(0.5)
        print(f"시리얼 연결: {SERIAL_PORT}")
        return True
    except Exception as e:
        print(f"시리얼 연결 실패: {e}")
        return False

def send_serial(cmd):
    global serial_conn
    if serial_conn and serial_conn.is_open:
        try:
            serial_conn.write(f"{cmd}\n".encode())
            serial_conn.flush()
            time.sleep(0.02)
            if serial_conn.in_waiting:
                response = serial_conn.readline().decode().strip()
                print(f"ESP32: {response}")
                return response.startswith("OK")
        except Exception as e:
            print(f"시리얼 오류: {e}")
    return False

# ========== mpg123 remote 모드 ==========
def play_track(track_name):
    global player_process, monitor_thread, playing, current_track
    global current_patterns, current_pattern_idx, track_duration

    stop_playback()

    track_path = os.path.join(MP3_DIR, track_name)
    if not os.path.exists(track_path):
        print(f"파일 없음: {track_path}")
        return False

    # 패턴 로드
    patterns_data = load_patterns()
    if track_name in patterns_data:
        current_patterns = sorted(patterns_data[track_name].get("patterns", []), key=lambda x: x["time"])
        track_duration = patterns_data[track_name].get("duration", 30)
    else:
        current_patterns = []
        track_duration = 30

    current_pattern_idx = 0

    # 첫 패턴 전송
    if current_patterns:
        send_serial(f"PATTERN:{current_patterns[0]['pattern']}")

    # mpg123 remote 모드로 실행
    try:
        player_process = subprocess.Popen(
            ['mpg123', '-R', '-a', 'hw:1,0'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )

        playing = True
        current_track = track_name

        # 파일 로드 명령
        player_process.stdin.write(f"LOAD {track_path}\n")
        player_process.stdin.flush()

        print(f"재생 시작: {track_name}")

        # 출력 모니터링 스레드 시작
        monitor_thread = threading.Thread(target=monitor_playback, args=(track_path,), daemon=True)
        monitor_thread.start()

        return True
    except Exception as e:
        print(f"재생 오류: {e}")
        return False

def monitor_playback(track_path):
    """mpg123 출력 모니터링 - 실제 재생 위치 추적"""
    global playing, current_pattern_idx, player_process

    # @F 파싱: @F <frame> <frames_left> <seconds> <seconds_left>
    frame_pattern = re.compile(r'@F\s+\d+\s+\d+\s+([\d.]+)\s+[\d.]+')

    while playing and player_process:
        try:
            line = player_process.stdout.readline()
            if not line:
                break

            line = line.strip()

            # @F: 프레임 정보 (현재 재생 위치)
            match = frame_pattern.match(line)
            if match:
                current_time = float(match.group(1))
                check_pattern_change(current_time)

            # @P 0: 재생 종료 (루프 재시작)
            elif line == "@P 0":
                print("트랙 종료 - 루프 재시작")
                current_pattern_idx = 0
                if current_patterns:
                    send_serial(f"PATTERN:{current_patterns[0]['pattern']}")
                # 다시 로드
                if playing and player_process:
                    player_process.stdin.write(f"LOAD {track_path}\n")
                    player_process.stdin.flush()

        except Exception as e:
            if playing:
                print(f"모니터링 오류: {e}")
            break

def check_pattern_change(current_time):
    """현재 재생 시간에 따라 패턴 변경"""
    global current_pattern_idx

    while current_pattern_idx < len(current_patterns):
        pattern_time = current_patterns[current_pattern_idx]["time"]

        if current_time >= pattern_time:
            pattern_num = current_patterns[current_pattern_idx]["pattern"]
            send_serial(f"PATTERN:{pattern_num}")
            current_pattern_idx += 1
        else:
            break

def stop_playback():
    global player_process, playing, current_track, current_pattern_idx

    playing = False
    current_track = ""
    current_pattern_idx = 0

    if player_process:
        try:
            player_process.stdin.write("QUIT\n")
            player_process.stdin.flush()
            player_process.wait(timeout=2)
        except:
            player_process.kill()
        player_process = None

    send_serial("STOP")
    print("재생 중지")

def get_state():
    if player_process and player_process.poll() is None:
        return "playing"
    return "stopped"

# ========== MQTT 콜백 ==========
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"MQTT 연결됨 (rc={rc})")
    client.subscribe(TOPIC_COMMAND)
    client.subscribe(TOPIC_TRACK)
    client.publish(TOPIC_STATE, get_state(), retain=True)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"MQTT 수신 [{topic}]: {payload}")

    if topic == TOPIC_COMMAND:
        if payload == "play":
            if current_track:
                play_track(current_track)
            client.publish(TOPIC_STATE, "playing", retain=True)
        elif payload == "stop":
            stop_playback()
            client.publish(TOPIC_STATE, "stopped", retain=True)
        elif payload == "status":
            client.publish(TOPIC_STATE, get_state(), retain=True)

    elif topic == TOPIC_TRACK:
        if payload:
            if play_track(payload):
                client.publish(TOPIC_STATE, "playing", retain=True)

# ========== 메인 ==========
def signal_handler(sig, frame):
    print("\n종료 중...")
    stop_playback()
    if serial_conn:
        serial_conn.close()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    init_serial()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"MQTT 브로커 연결: {MQTT_BROKER}")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    client.loop_forever()

if __name__ == "__main__":
    main()
