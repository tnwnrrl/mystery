#!/usr/bin/env python3
"""
macOS MQTT MP3 Player (mac.py)
Home Assistant에서 MQTT로 macOS MP3 재생 제어

토픽:
- macos_mp3/track → 파일명 수신 시 재생
- macos_mp3/command → stop / status
- macos_mp3/state → playing / stopped (상태 발행)
"""

import paho.mqtt.client as mqtt
import subprocess
import threading
import os
import signal
import sys

# ========== 설정 ==========
MQTT_BROKER = "192.168.0.25"
MQTT_PORT = 1883
MQTT_USER = "mystery"
MQTT_PASSWORD = "qwerqwer"

# MP3 파일 경로
MP3_DIR = os.path.expanduser("~/Music/ha_mp3")

# MQTT 토픽
TOPIC_TRACK = "macos_mp3/track"
TOPIC_TRACK_ONCE = "macos_mp3/track_once"  # 단일 재생
TOPIC_COMMAND = "macos_mp3/command"
TOPIC_STATE = "macos_mp3/state"

# ========== 전역 변수 ==========
player_process = None
monitor_thread = None
mqtt_client = None
current_track = ""
loop_enabled = True  # 반복 재생 활성화
stop_requested = False  # 정지 요청 플래그

# ========== MP3 재생 ==========
def play_mp3(filename, loop=True):
    """MP3 재생. loop=True면 반복, False면 단일 재생"""
    global player_process, monitor_thread, current_track, stop_requested

    stop_mp3()
    stop_requested = False

    filepath = os.path.join(MP3_DIR, filename)
    if not os.path.exists(filepath):
        print(f"파일 없음: {filepath}")
        return False

    try:
        if loop:
            # 셸 루프로 끊김 최소화
            player_process = subprocess.Popen(
                f'while true; do afplay "{filepath}"; done',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # 프로세스 그룹으로 관리
            )
        else:
            player_process = subprocess.Popen(
                ["afplay", filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        current_track = filename
        print(f"재생 시작: {filename}" + (" (반복)" if loop else " (단일)"))

        # 단일 재생 시에만 완료 모니터링
        if not loop:
            monitor_thread = threading.Thread(target=monitor_playback, daemon=True)
            monitor_thread.start()

        return True
    except Exception as e:
        print(f"재생 오류: {e}")
        return False

def stop_mp3():
    global player_process, current_track, stop_requested

    stop_requested = True

    # 1. 프로세스 그룹 종료 시도
    if player_process:
        try:
            os.killpg(os.getpgid(player_process.pid), signal.SIGTERM)
            player_process.wait(timeout=2)
        except:
            try:
                os.killpg(os.getpgid(player_process.pid), signal.SIGKILL)
            except:
                pass
        player_process = None

    # 2. 남은 afplay 프로세스 강제 종료
    try:
        subprocess.run(["pkill", "-9", "afplay"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "while true.*afplay"], capture_output=True)
    except:
        pass

    current_track = ""
    print("재생 중지")

def monitor_playback():
    """단일 재생 완료 시 상태 업데이트"""
    global player_process, mqtt_client, stop_requested

    if player_process:
        player_process.wait()
        if mqtt_client and mqtt_client.is_connected() and not stop_requested:
            # 정상 완료 시 finished, stop 명령 시 stopped
            mqtt_client.publish(TOPIC_STATE, "finished", retain=True)
            print("재생 완료 (finished)")

# ========== MQTT 콜백 ==========
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"MQTT 연결됨: {MQTT_BROKER}")
        client.subscribe(TOPIC_TRACK)
        client.subscribe(TOPIC_TRACK_ONCE)
        client.subscribe(TOPIC_COMMAND)
        client.publish(TOPIC_STATE, "stopped", retain=True)
    else:
        print(f"MQTT 연결 실패: {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode().strip()
    print(f"수신 [{topic}]: {payload}")

    if topic == TOPIC_TRACK:
        # 반복 재생
        if payload:
            if play_mp3(payload, loop=True):
                client.publish(TOPIC_STATE, "playing", retain=True)
            else:
                client.publish(TOPIC_STATE, "error", retain=True)

    elif topic == TOPIC_TRACK_ONCE:
        # 단일 재생
        if payload:
            if play_mp3(payload, loop=False):
                client.publish(TOPIC_STATE, "playing", retain=True)
            else:
                client.publish(TOPIC_STATE, "error", retain=True)

    elif topic == TOPIC_COMMAND:
        cmd = payload.lower()
        if cmd == "stop":
            stop_mp3()
            client.publish(TOPIC_STATE, "stopped", retain=True)
        elif cmd == "status":
            state = "playing" if player_process and player_process.poll() is None else "stopped"
            client.publish(TOPIC_STATE, state, retain=True)
            print(f"상태: {state}, 트랙: {current_track or 'none'}")

# ========== 종료 처리 ==========
def signal_handler(sig, frame):
    print("\n종료 중...")
    stop_mp3()
    if mqtt_client:
        mqtt_client.publish(TOPIC_STATE, "offline", retain=True)
        mqtt_client.disconnect()
    sys.exit(0)

# ========== 메인 ==========
def main():
    global mqtt_client

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # MP3 디렉토리 생성
    os.makedirs(MP3_DIR, exist_ok=True)
    print(f"MP3 디렉토리: {MP3_DIR}")
    print(f"MQTT 브로커: {MQTT_BROKER}")

    # MQTT 클라이언트
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        print("MQTT 연결 중...")
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"오류: {e}")
    finally:
        stop_mp3()
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()
