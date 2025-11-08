#!/usr/bin/env python3
"""
Canon 100D 사진 자동 처리 메인 프로그램

기능:
1. 카메라에서 실시간으로 새 사진 감지
2. 자동으로 사진 다운로드
3. PNG 레이어 합성
4. 최종 출력 폴더에 저장
"""

import os
import sys
import json
import time
from datetime import datetime
from utils.camera import CameraConnection
from utils.image_processor import ImageProcessor


class PhotoProcessor:
    """사진 자동 처리 메인 클래스"""

    def __init__(self, config_path: str = "config.json"):
        """설정 파일 로드"""
        # 설정 로드
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 경로 설정
        self.original_folder = self.config['paths']['original_folder']
        self.overlay_image = self.config['paths']['overlay_image']
        self.output_folder = self.config['paths']['output_folder']

        # 모니터링 설정
        self.check_interval = self.config['camera']['check_interval_seconds']
        self.processed_files_db = self.config['monitoring']['processed_files_db']

        # 처리된 파일 목록 로드
        self.processed_files = self.load_processed_files()

        # 이미지 프로세서 초기화
        self.image_processor = ImageProcessor(self.overlay_image)

    def load_processed_files(self) -> set:
        """처리된 파일 목록 로드"""
        if os.path.exists(self.processed_files_db):
            with open(self.processed_files_db, 'r') as f:
                return set(json.load(f))
        return set()

    def save_processed_files(self):
        """처리된 파일 목록 저장"""
        with open(self.processed_files_db, 'w') as f:
            json.dump(list(self.processed_files), f, indent=2)

    def process_new_photos(self, new_files: list) -> int:
        """새로운 사진들을 처리"""
        if not new_files:
            return 0

        print(f"\n🖼️  PNG 레이어 합성 시작... (총 {len(new_files)}개)")

        processed_count = 0
        for filename in new_files:
            input_path = os.path.join(self.original_folder, filename)
            output_path = os.path.join(self.output_folder, filename)

            if self.image_processor.composite_image(input_path, output_path):
                processed_count += 1

        return processed_count

    def run_once(self):
        """1회 실행 모드"""
        print("=" * 60)
        print("Canon 100D 사진 자동 처리 (1회 실행 모드)")
        print("=" * 60)

        with CameraConnection() as camera:
            if not camera.is_connected:
                print("❌ 카메라 연결 실패")
                return

            print("\n📥 새로운 파일 다운로드 중...")
            new_files = camera.download_new_files(
                self.original_folder,
                self.processed_files
            )

            if not new_files:
                print("⚠️ 새로운 파일이 없습니다.")
                return

            print(f"✅ {len(new_files)}개 파일 다운로드 완료")

            # 카메라 내 파일 경로를 처리됨으로 표시
            all_files = camera.get_all_files()
            for file_info in all_files:
                if file_info['name'] in new_files:
                    self.processed_files.add(file_info['full_path'])

            # PNG 합성 처리
            processed = self.process_new_photos(new_files)

            print(f"\n📊 처리 완료:")
            print(f"  다운로드: {len(new_files)}개")
            print(f"  합성 완료: {processed}개")
            print(f"  저장 위치: {os.path.abspath(self.output_folder)}")

            # 처리된 파일 목록 저장
            self.save_processed_files()

    def run_monitor(self):
        """실시간 모니터링 모드"""
        print("=" * 60)
        print("Canon 100D 사진 자동 처리 (실시간 모니터링 모드)")
        print("=" * 60)
        print(f"⏱️  감지 간격: {self.check_interval}초")
        print("📋 Ctrl+C를 눌러 종료\n")

        try:
            while True:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] 카메라 확인 중...", end=" ")

                try:
                    with CameraConnection() as camera:
                        if not camera.is_connected:
                            print("❌ 연결 실패")
                            time.sleep(self.check_interval)
                            continue

                        # 새 파일 다운로드
                        new_files = camera.download_new_files(
                            self.original_folder,
                            self.processed_files
                        )

                        if new_files:
                            print(f"\n✅ 새 파일 {len(new_files)}개 발견!")

                            # 카메라 내 파일 경로를 처리됨으로 표시
                            all_files = camera.get_all_files()
                            for file_info in all_files:
                                if file_info['name'] in new_files:
                                    self.processed_files.add(file_info['full_path'])

                            # PNG 합성 처리
                            processed = self.process_new_photos(new_files)

                            print(f"✅ {processed}개 파일 처리 완료\n")

                            # 처리된 파일 목록 저장
                            self.save_processed_files()
                        else:
                            print("✓")

                except Exception as e:
                    print(f"❌ 오류: {e}")

                # 대기
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n⚠️ 모니터링 종료")


def main():
    """메인 실행 함수"""
    # 설정 파일 확인
    if not os.path.exists("config.json"):
        print("❌ config.json 파일을 찾을 수 없습니다.")
        sys.exit(1)

    # 프로세서 초기화
    processor = PhotoProcessor()

    # 실행 모드 선택
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        processor.run_monitor()
    else:
        processor.run_once()


if __name__ == "__main__":
    main()
