#!/usr/bin/env python3
"""
MQTT Video Player with Pygame (Black Screen)
항상 검은 전체화면 유지, 영상 재생 시에만 표시

토픽:
- old_tv/video → 파일명 수신 시 반복 재생
- old_tv/video_once → 파일명 수신 시 단일 재생 (종료 시 finished 발행)
- old_tv/command → play / stop / status
- old_tv/state → playing / stopped / finished (상태 발행)
"""

import os
import sys
import signal
import threading
import time

import pygame
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

# 화면 설정
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# ========== 전역 변수 ==========
mqtt_client = None
vlc_instance = None
vlc_player = None
current_video = ""
is_loop_mode = True
is_playing = False
screen = None
running = True


# ========== Pygame 초기화 ==========
def init_pygame():
    """Pygame 전체화면 검은 창 초기화"""
    global screen

    # SDL 환경 변수 (라즈베리파이용)
    os.environ['SDL_VIDEODRIVER'] = 'x11'

    pygame.init()
    pygame.mouse.set_visible(False)

    # 전체화면 검은 창
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Video Player")
    screen.fill((0, 0, 0))
    pygame.display.flip()

    print(f"Pygame 초기화: {SCREEN_WIDTH}x{SCREEN_HEIGHT} 전체화면")


# ========== VLC 초기화 ==========
def init_vlc():
    """VLC 인스턴스 초기화 (Pygame 창에 임베드)"""
    global vlc_instance, vlc_player

    # VLC 인스턴스 생성
    vlc_instance = vlc.Instance([
        '--no-xlib',
        '--quiet',
        '--no-osd',
        '--vout=xcb_x11',  # OpenGL 대신 X11 출력
        '--aout=alsa',
        '--alsa-audio-device=hw:0,0',  # HDMI 오디오
    ])

    vlc_player = vlc_instance.media_player_new()

    # Pygame 창에 VLC 출력 연결
    win_id = pygame.display.get_wm_info()['window']
    vlc_player.set_xwindow(win_id)

    # 이벤트 매니저 설정
    events = vlc_player.event_manager()
    events.event_attach(vlc.EventType.MediaPlayerEndReached, on_video_end)

    print("VLC 초기화 완료")


def on_video_end(event):
    """영상 재생 완료 콜백"""
    global is_playing, mqtt_client, is_loop_mode

    if is_loop_mode:
        # 반복 재생: 다시 시작
        if vlc_player:
            vlc_player.stop()
            vlc_player.play()
    else:
        # 단일 재생: 종료 및 finished 발행
        is_playing = False
        clear_screen()

        if mqtt_client and mqtt_client.is_connected():
            mqtt_client.publish(TOPIC_STATE, "finished", retain=True)
            print("재생 완료 (finished)")


# ========== 영상 제어 ==========
def play_video(filename, loop=True):
    """영상 재생"""
    global vlc_player, current_video, is_loop_mode, is_playing

    stop_video()

    filepath = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(filepath):
        print(f"파일 없음: {filepath}")
        return False

    is_loop_mode = loop
    current_video = filename

    try:
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
    """영상 정지"""
    global vlc_player, current_video, is_playing

    if vlc_player:
        vlc_player.stop()

    is_playing = False
    current_video = ""
    clear_screen()
    print("재생 중지")


def clear_screen():
    """검은 화면으로 초기화"""
    global screen
    if screen:
        screen.fill((0, 0, 0))
        pygame.display.flip()


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
            state = "playing" if is_playing else "stopped"
            client.publish(TOPIC_STATE, state, retain=True)
            print(f"상태: {state}, 영상: {current_video or 'none'}")


# ========== MQTT 스레드 ==========
def mqtt_thread():
    """MQTT 클라이언트 별도 스레드"""
    global mqtt_client

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"MQTT 오류: {e}")


# ========== 메인 루프 ==========
def main_loop():
    """Pygame 메인 이벤트 루프"""
    global running

    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_q:
                    running = False

        # 재생 중이 아니면 검은 화면 유지
        if not is_playing:
            clear_screen()

        clock.tick(30)


# ========== 종료 처리 ==========
def cleanup():
    """정리"""
    global running, vlc_player, mqtt_client

    running = False

    if vlc_player:
        vlc_player.stop()

    if mqtt_client:
        mqtt_client.publish(TOPIC_STATE, "offline", retain=True)
        mqtt_client.disconnect()

    pygame.quit()
    print("종료 완료")


def signal_handler(sig, frame):
    print("\n종료 중...")
    cleanup()
    sys.exit(0)


# ========== 메인 ==========
def main():
    global running

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 비디오 디렉토리 확인
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR, exist_ok=True)

    print(f"비디오 디렉토리: {VIDEO_DIR}")
    print(f"MQTT 브로커: {MQTT_BROKER}")
    print("ESC 또는 Q로 종료")

    # 초기화
    init_pygame()
    init_vlc()

    # MQTT 스레드 시작
    mqtt_t = threading.Thread(target=mqtt_thread, daemon=True)
    mqtt_t.start()

    # 메인 루프
    try:
        main_loop()
    except Exception as e:
        print(f"오류: {e}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
