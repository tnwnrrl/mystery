#!/usr/bin/env python3
"""
MQTT Video Player for Raspberry Pi
VLC로 HDMI 영상 재생, Home Assistant MQTT 연동

토픽:
- old_tv/video → 파일명 수신 시 반복 재생
- old_tv/video_once → 파일명 수신 시 단일 재생 (종료 시 finished 발행)
- old_tv/command → play / stop / status
- old_tv/state → playing / stopped / finished (상태 발행)
"""

import paho.mqtt.client as mqtt
import subprocess
import threading
import os
import signal
import sys
import time

# ========== 설정 ==========
MQTT_BROKER = "192.168.0.100"
MQTT_PORT = 1883
MQTT_USER = "mystery"
MQTT_PASSWORD = "qwerqwer"

VIDEO_DIR = "/home/pi/videos"

# MQTT 토픽
TOPIC_VIDEO = "old_tv/video"
TOPIC_VIDEO_ONCE = "old_tv/video_once"  # 단일 재생
TOPIC_COMMAND = "old_tv/command"
TOPIC_STATE = "old_tv/state"

# ========== 전역 변수 ==========
player_process = None
monitor_thread = None
mqtt_client = None
current_video = ""
is_loop_mode = True

# ========== 영상 재생 ==========
def play_video(filename, loop=True):
    """영상 재생. loop=True면 반복, False면 단일 재생"""
    global player_process, monitor_thread, current_video, is_loop_mode

    stop_video()

    filepath = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(filepath):
        print(f"파일 없음: {filepath}")
        return False

    is_loop_mode = loop

    try:
        # VLC 명령 구성
        cmd = [
            "cvlc",  # VLC 헤드리스 모드
            "--fullscreen",
            "--no-osd",
            "--aout=alsa",
            "--alsa-audio-device=hw:0,0",  # HDMI 오디오
        ]

        if loop:
            cmd.append("--loop")

        cmd.append(filepath)

        player_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        current_video = filename
        print(f"재생 시작: {filename}" + (" (반복)" if loop else " (단일)"))

        # 단일 재생 시 완료 모니터링
        if not loop:
            monitor_thread = threading.Thread(target=monitor_playback, daemon=True)
            monitor_thread.start()

        return True
    except Exception as e:
        print(f"재생 오류: {e}")
        return False


def stop_video():
    """영상 정지"""
    global player_process, current_video

    if player_process:
        try:
            player_process.terminate()
            player_process.wait(timeout=3)
        except:
            player_process.kill()
        player_process = None

    # 남은 VLC 프로세스 정리
    try:
        subprocess.run(["pkill", "-9", "vlc"], capture_output=True)
    except:
        pass

    current_video = ""
    print("재생 중지")


def monitor_playback():
    """단일 재생 완료 모니터링"""
    global player_process, mqtt_client

    if player_process:
        player_process.wait()  # 프로세스 종료 대기

        if mqtt_client and mqtt_client.is_connected():
            mqtt_client.publish(TOPIC_STATE, "finished", retain=True)
            print("재생 완료 (finished)")


# ========== MQTT 콜백 ==========
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"MQTT 연결됨: {MQTT_BROKER}")
        client.subscribe(TOPIC_VIDEO)
        client.subscribe(TOPIC_VIDEO_ONCE)
        client.subscribe(TOPIC_COMMAND)
        client.publish(TOPIC_STATE, "stopped", retain=True)
    else:
        print(f"MQTT 연결 실패: {rc}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode().strip()
    print(f"수신 [{topic}]: {payload}")

    if topic == TOPIC_VIDEO:
        # 반복 재생
        if payload:
            if play_video(payload, loop=True):
                client.publish(TOPIC_STATE, "playing", retain=True)
            else:
                client.publish(TOPIC_STATE, "error", retain=True)

    elif topic == TOPIC_VIDEO_ONCE:
        # 단일 재생
        if payload:
            if play_video(payload, loop=False):
                client.publish(TOPIC_STATE, "playing", retain=True)
            else:
                client.publish(TOPIC_STATE, "error", retain=True)

    elif topic == TOPIC_COMMAND:
        cmd = payload.lower()
        if cmd == "play":
            if current_video:
                if play_video(current_video, loop=is_loop_mode):
                    client.publish(TOPIC_STATE, "playing", retain=True)
        elif cmd == "stop":
            stop_video()
            client.publish(TOPIC_STATE, "stopped", retain=True)
        elif cmd == "status":
            if player_process and player_process.poll() is None:
                state = "playing"
            else:
                state = "stopped"
            client.publish(TOPIC_STATE, state, retain=True)
            print(f"상태: {state}, 영상: {current_video or 'none'}")


# ========== 종료 처리 ==========
def signal_handler(sig, frame):
    print("\n종료 중...")
    stop_video()
    if mqtt_client:
        mqtt_client.publish(TOPIC_STATE, "offline", retain=True)
        mqtt_client.disconnect()
    sys.exit(0)


# ========== 메인 ==========
def main():
    global mqtt_client

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 비디오 디렉토리 확인
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR, exist_ok=True)
    print(f"비디오 디렉토리: {VIDEO_DIR}")
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
        stop_video()
        mqtt_client.disconnect()


if __name__ == "__main__":
    main()
