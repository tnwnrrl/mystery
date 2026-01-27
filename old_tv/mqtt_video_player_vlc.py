#!/usr/bin/env python3
"""
MQTT Video Player - VLC 창 유지 방식
영상 전환 시에도 VLC 창을 닫지 않고 검은 화면 유지

토픽:
- old_tv/video → 파일명 수신 시 반복 재생
- old_tv/video_once → 파일명 수신 시 단일 재생 (종료 시 finished 발행)
- old_tv/command → play / stop / status
- old_tv/state → playing / stopped / finished (상태 발행)
"""

import os
import sys
import signal
import time

import vlc
import paho.mqtt.client as mqtt

# ========== 설정 ==========
MQTT_BROKER = "192.168.0.100"
MQTT_PORT = 1883
MQTT_USER = "mystery"
MQTT_PASSWORD = "qwerqwer"

VIDEO_DIR = "/home/pi/videos"

# MQTT 토픽
TOPIC_VIDEO = "old_tv/video"
TOPIC_VIDEO_ONCE = "old_tv/video_once"
TOPIC_COMMAND = "old_tv/command"
TOPIC_STATE = "old_tv/state"

# ========== 전역 변수 ==========
mqtt_client = None
vlc_instance = None
vlc_player = None
current_video = ""
is_loop_mode = True
is_playing = False
running = True


# ========== VLC 초기화 ==========
def init_vlc():
    """VLC 인스턴스 초기화 - 전체화면 검은 창"""
    global vlc_instance, vlc_player

    vlc_instance = vlc.Instance([
        '--fullscreen',
        '--no-osd',
        '--no-video-title-show',
        '--aout=alsa',
        '--alsa-audio-device=hw:0,0',
        '--video-on-top',
        '--drawable-xid=0',  # root window에 그리기
    ])

    vlc_player = vlc_instance.media_player_new()
    vlc_player.set_fullscreen(True)

    # 이벤트 핸들러 등록
    events = vlc_player.event_manager()
    events.event_attach(vlc.EventType.MediaPlayerEndReached, on_video_end)

    print("VLC 초기화 완료 (전체화면)")


def on_video_end(event):
    """영상 재생 완료 콜백"""
    global is_playing, is_loop_mode

    if is_loop_mode:
        # 반복 재생
        if vlc_player and current_video:
            vlc_player.stop()
            time.sleep(0.1)
            vlc_player.play()
    else:
        # 단일 재생 완료
        is_playing = False
        if mqtt_client and mqtt_client.is_connected():
            mqtt_client.publish(TOPIC_STATE, "finished", retain=True)
            print("재생 완료 (finished)")


# ========== 영상 제어 ==========
def play_video(filename, loop=True):
    """영상 재생 - VLC 창 유지"""
    global current_video, is_loop_mode, is_playing

    filepath = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(filepath):
        print(f"파일 없음: {filepath}")
        return False

    is_loop_mode = loop
    current_video = filename

    try:
        # 기존 재생 중지 (창은 유지)
        vlc_player.stop()
        time.sleep(0.1)

        # 새 미디어 설정
        media = vlc_instance.media_new(filepath)
        vlc_player.set_media(media)
        vlc_player.play()
        is_playing = True

        print(f"재생 시작: {filename}" + (" (반복)" if loop else " (단일)"))
        return True

    except Exception as e:
        print(f"재생 오류: {e}")
        return False


def stop_video():
    """영상 정지 - VLC 창은 유지 (검은 화면)"""
    global is_playing, current_video

    if vlc_player:
        vlc_player.stop()

    is_playing = False
    current_video = ""
    print("재생 중지 (검은 화면 유지)")


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
        if payload:
            if play_video(payload, loop=True):
                client.publish(TOPIC_STATE, "playing", retain=True)
            else:
                client.publish(TOPIC_STATE, "error", retain=True)

    elif topic == TOPIC_VIDEO_ONCE:
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
            state = "playing" if is_playing else "stopped"
            client.publish(TOPIC_STATE, state, retain=True)
            print(f"상태: {state}, 영상: {current_video or 'none'}")


# ========== 종료 처리 ==========
def cleanup():
    global running, vlc_player, mqtt_client

    running = False

    if vlc_player:
        vlc_player.stop()
        vlc_player.release()

    if vlc_instance:
        vlc_instance.release()

    if mqtt_client:
        mqtt_client.publish(TOPIC_STATE, "offline", retain=True)
        mqtt_client.disconnect()

    print("종료 완료")


def signal_handler(sig, frame):
    print("\n종료 중...")
    cleanup()
    sys.exit(0)


# ========== 메인 ==========
def main():
    global mqtt_client

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR, exist_ok=True)

    print(f"비디오 디렉토리: {VIDEO_DIR}")
    print(f"MQTT 브로커: {MQTT_BROKER}")

    # VLC 초기화
    init_vlc()

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
        cleanup()


if __name__ == "__main__":
    main()
