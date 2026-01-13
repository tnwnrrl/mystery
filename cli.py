#!/usr/bin/env python3
"""
CLI 모드 이미지 처리기
- tkinter 없이 실행 가능
- 카메라 모니터링 + 자동 다운로드 + 합성
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# 현재 디렉토리를 모듈 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.ai_transformer import HybridProcessor, check_internet
from utils.image_processor import ImageProcessor

# 카메라 모듈 (gphoto2 없으면 None)
try:
    from utils.camera import CameraConnection
    CAMERA_AVAILABLE = True
except ImportError:
    CameraConnection = None
    CAMERA_AVAILABLE = False


def load_config(config_path: str = "config.json") -> dict:
    """설정 파일 로드"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_processed_files(processed_files: set, filepath: str):
    """처리된 파일 목록 저장"""
    with open(filepath, 'w') as f:
        json.dump(list(processed_files), f)


def load_processed_files(filepath: str) -> set:
    """처리된 파일 목록 로드"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return set(json.load(f))
    return set()


def process_single_file(processor: HybridProcessor, input_path: str, output_dir: str) -> bool:
    """단일 파일 처리"""
    if not os.path.exists(input_path):
        print(f"❌ 파일 없음: {input_path}")
        return False

    filename = os.path.basename(input_path)
    output_path = os.path.join(output_dir, f"processed_{filename}")

    print(f"🔄 처리 중: {filename}")
    success, method, message = processor.process_image(input_path, output_path)

    if success:
        print(f"✅ 완료 [{method}]: {message}")
        print(f"   출력: {output_path}")
    else:
        print(f"❌ 실패 [{method}]: {message}")

    return success


def kill_camera_daemons():
    """macOS 카메라 데몬 종료"""
    import subprocess
    daemons = ["ptpcamerad", "mscamerad", "icdd", "cameracaptured"]
    for daemon in daemons:
        subprocess.run(["pkill", "-9", "-f", daemon], capture_output=True)
    time.sleep(1)


def monitor_camera(processor: HybridProcessor, config: dict, interval: float = 5.0):
    """카메라 모니터링 모드 - 카메라에서 직접 파일 가져와서 처리"""
    if not CAMERA_AVAILABLE:
        print("❌ gphoto2가 설치되지 않아 카메라 모니터링 불가")
        print("   폴더 모니터링 모드를 사용하세요: python3 cli.py monitor-folder")
        return

    download_dir = config.get('paths', {}).get('original_folder', 'downloaded_photos')
    output_dir = config.get('paths', {}).get('output_folder', 'processed_photos')
    processed_db = config.get('monitoring', {}).get('processed_files_db', 'processed_files.json')

    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    processed_files = load_processed_files(processed_db)

    print("=" * 50)
    print("📸 카메라 모니터링 모드")
    print("=" * 50)
    print(f"📁 다운로드: {download_dir}")
    print(f"📁 출력: {output_dir}")
    print(f"⏱️  확인 간격: {interval}초")
    print("   Ctrl+C로 중지\n")

    # 카메라 데몬 종료
    print("🔧 카메라 데몬 종료 중...")
    kill_camera_daemons()

    camera = None
    retry_count = 0
    max_retries = 3

    try:
        while True:
            # 카메라 연결
            if camera is None:
                print("📷 카메라 연결 시도...")
                camera = CameraConnection()
                if camera.connect():
                    print(f"✅ 카메라 연결: {camera.camera_name}")
                    retry_count = 0
                else:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"❌ 카메라 연결 실패 ({max_retries}회 시도)")
                        print("   USB 케이블을 확인하고 다시 시도하세요")
                        kill_camera_daemons()
                        retry_count = 0
                    camera = None
                    time.sleep(interval)
                    continue

            # 카메라에서 파일 목록 가져오기
            try:
                camera_files = camera.get_all_files()
            except Exception as e:
                print(f"⚠️ 파일 목록 가져오기 실패: {e}")
                camera.disconnect()
                camera = None
                continue

            # 새 파일 확인 및 처리
            for file_info in camera_files:
                # file_info는 dict: {'path': ..., 'name': ..., 'full_path': ...}
                filename = file_info['name']

                # 이미 처리된 파일 스킵
                if filename in processed_files:
                    continue

                # JPG만 처리
                if not filename.lower().endswith(('.jpg', '.jpeg')):
                    continue

                print(f"\n🆕 새 파일 발견: {filename}")

                # 다운로드
                local_path = os.path.join(download_dir, filename)
                try:
                    if camera.download_file(file_info, download_dir):
                        print(f"   📥 다운로드 완료: {local_path}")
                    else:
                        print(f"   ❌ 다운로드 실패")
                        continue
                except Exception as e:
                    print(f"   ❌ 다운로드 오류: {e}")
                    continue

                # 처리
                output_path = os.path.join(output_dir, filename)
                success, method, message = processor.process_image(local_path, output_path)

                if success:
                    print(f"   ✅ 처리 완료 [{method}]: {message}")
                    processed_files.add(filename)
                    save_processed_files(processed_files, processed_db)
                else:
                    print(f"   ❌ 처리 실패 [{method}]: {message}")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n🛑 모니터링 중지")
    finally:
        if camera:
            camera.disconnect()
            print("📷 카메라 연결 해제")


def monitor_folder(processor: HybridProcessor, input_dir: str, output_dir: str,
                   processed_file: str = "processed_files.json", interval: float = 2.0):
    """폴더 모니터링 모드"""
    print("=" * 50)
    print("📁 폴더 모니터링 모드")
    print("=" * 50)
    print(f"📁 입력: {input_dir}")
    print(f"📁 출력: {output_dir}")
    print(f"⏱️  확인 간격: {interval}초")
    print("   Ctrl+C로 중지\n")

    processed_files = load_processed_files(processed_file)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(input_dir, exist_ok=True)

    try:
        while True:
            for filename in os.listdir(input_dir):
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue

                if filename in processed_files:
                    continue

                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, f"processed_{filename}")

                print(f"\n🆕 새 파일 발견: {filename}")
                success, method, message = processor.process_image(input_path, output_path)

                if success:
                    print(f"✅ 완료 [{method}]: {message}")
                    processed_files.add(filename)
                    save_processed_files(processed_files, processed_file)
                else:
                    print(f"❌ 실패 [{method}]: {message}")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n🛑 모니터링 중지")


def show_status(config: dict):
    """현재 상태 표시"""
    print("=" * 50)
    print("📊 시스템 상태")
    print("=" * 50)

    # 카메라
    print(f"📷 카메라 모듈: {'✅ gphoto2 사용 가능' if CAMERA_AVAILABLE else '❌ gphoto2 없음'}")

    # 인터넷 연결
    internet = check_internet()
    print(f"🌐 인터넷: {'✅ 연결됨' if internet else '❌ 연결 안됨'}")

    # AI 설정
    ai_config = config.get('ai', {})
    print(f"🤖 AI API 키: {'✅ 설정됨' if ai_config.get('api_key') else '❌ 미설정'}")
    print(f"🤖 AI 모델: {ai_config.get('model', '미설정')}")

    # 처리 모드
    mode = config.get('processing', {}).get('mode', 'hybrid')
    print(f"⚙️  처리 모드: {mode}")

    # 오버레이 이미지
    overlay_path = config.get('paths', {}).get('overlay_image', '')
    overlay_exists = os.path.exists(overlay_path) if overlay_path else False
    print(f"🎨 오버레이: {'✅ ' + overlay_path if overlay_exists else '❌ 미설정'}")

    # HybridProcessor 상태
    if ai_config.get('api_key') or overlay_exists:
        processor = HybridProcessor(config)
        status = processor.get_status()
        print(f"\n📋 HybridProcessor 상태:")
        print(f"   AI 사용 가능: {'✅' if status['ai_available'] else '❌'} ({status['ai_reason']})")
        print(f"   오버레이 사용 가능: {'✅' if status['overlay_available'] else '❌'}")

    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description='이미지 처리 CLI')
    parser.add_argument('--config', '-c', default='config.json', help='설정 파일 경로')
    parser.add_argument('--mode', '-m', choices=['ai', 'overlay', 'hybrid'], help='처리 모드')
    parser.add_argument('--status', '-s', action='store_true', help='상태 확인')

    subparsers = parser.add_subparsers(dest='command')

    # 단일 파일 처리
    process_parser = subparsers.add_parser('process', help='단일 파일 처리')
    process_parser.add_argument('input', help='입력 이미지 경로')
    process_parser.add_argument('--output-dir', '-o', default='processed_photos', help='출력 폴더')

    # 카메라 모니터링 (기본)
    camera_parser = subparsers.add_parser('monitor', help='카메라 모니터링 (자동 다운로드 + 처리)')
    camera_parser.add_argument('--interval', '-t', type=float, default=5.0, help='확인 간격(초)')

    # 폴더 모니터링
    folder_parser = subparsers.add_parser('monitor-folder', help='폴더 모니터링')
    folder_parser.add_argument('--input-dir', '-i', default='downloaded_photos', help='입력 폴더')
    folder_parser.add_argument('--output-dir', '-o', default='processed_photos', help='출력 폴더')
    folder_parser.add_argument('--interval', '-t', type=float, default=2.0, help='확인 간격(초)')

    args = parser.parse_args()

    # 설정 로드
    config = load_config(args.config)

    # 모드 오버라이드
    if args.mode:
        if 'processing' not in config:
            config['processing'] = {}
        config['processing']['mode'] = args.mode

    # 상태 확인
    if args.status:
        show_status(config)
        return

    # 명령이 없으면 상태 표시
    if not args.command:
        show_status(config)
        print("\n사용법:")
        print("  python3 cli.py monitor          # 카메라 모니터링 (자동)")
        print("  python3 cli.py monitor-folder   # 폴더 모니터링")
        print("  python3 cli.py process <파일>   # 단일 파일 처리")
        print("  python3 cli.py --status         # 상태 확인")
        return

    # 프로세서 초기화
    processor = HybridProcessor(config)
    status = processor.get_status()

    print(f"⚙️  모드: {status['mode']}")
    print(f"🤖 AI: {'✅' if status['ai_available'] else '❌'} ({status['ai_reason']})")
    print(f"🎨 오버레이: {'✅' if status['overlay_available'] else '❌'}")
    print()

    if args.command == 'process':
        process_single_file(processor, args.input, args.output_dir)

    elif args.command == 'monitor':
        monitor_camera(processor, config, interval=args.interval)

    elif args.command == 'monitor-folder':
        input_dir = args.input_dir
        output_dir = args.output_dir
        monitor_folder(processor, input_dir, output_dir, interval=args.interval)


if __name__ == '__main__':
    main()
