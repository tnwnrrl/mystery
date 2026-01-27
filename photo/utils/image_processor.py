"""
이미지 처리 및 PNG 레이어 합성 모듈
"""

import os
from PIL import Image
from typing import Optional


class ImageProcessor:
    """이미지 처리 및 합성 클래스"""

    def __init__(self, overlay_path: str):
        """
        Args:
            overlay_path: PNG 오버레이 이미지 경로
        """
        self.overlay_path = overlay_path
        self.overlay_image = None

        # 오버레이 이미지 로드
        if os.path.exists(overlay_path):
            self.overlay_image = Image.open(overlay_path)
            print(f"✅ 오버레이 이미지 로드: {overlay_path}")
        else:
            print(f"⚠️ 오버레이 이미지를 찾을 수 없습니다: {overlay_path}")

    def composite_image(
        self,
        base_image_path: str,
        output_path: str,
        overlay_mode: str = "fullscreen"
    ) -> bool:
        """
        베이스 이미지에 PNG 오버레이를 합성

        Args:
            base_image_path: 원본 이미지 경로
            output_path: 합성된 이미지 저장 경로
            overlay_mode: 합성 모드 ('fullscreen', 'fit', 'stretch')

        Returns:
            성공 여부
        """
        if not self.overlay_image:
            print("❌ 오버레이 이미지가 로드되지 않았습니다.")
            return False

        try:
            # 베이스 이미지 열기
            base_image = Image.open(base_image_path)

            # RGB 모드로 변환 (RGBA가 아닌 경우)
            if base_image.mode != 'RGB':
                base_image = base_image.convert('RGB')

            # 오버레이 이미지 크기 조정
            overlay = self.overlay_image.copy()

            if overlay_mode == "fullscreen":
                # 베이스 이미지와 같은 크기로 조정
                overlay = overlay.resize(base_image.size, Image.Resampling.LANCZOS)

            # 오버레이가 RGBA 모드인지 확인
            if overlay.mode == 'RGBA':
                # 알파 채널을 사용해서 합성
                # 베이스 이미지를 RGBA로 변환
                base_rgba = base_image.convert('RGBA')

                # 알파 합성
                composited = Image.alpha_composite(base_rgba, overlay)

                # RGB로 다시 변환 (JPEG 저장을 위해)
                result = composited.convert('RGB')
            else:
                # 알파 채널이 없으면 단순 붙여넣기
                result = base_image.copy()
                result.paste(overlay, (0, 0))

            # 출력 폴더 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 결과 저장
            result.save(output_path, 'JPEG', quality=95)

            return True

        except Exception as e:
            print(f"❌ 이미지 합성 실패 ({base_image_path}): {e}")
            return False

    def process_folder(
        self,
        input_folder: str,
        output_folder: str,
        file_list: Optional[list] = None
    ) -> int:
        """
        폴더 내 이미지들을 일괄 처리

        Args:
            input_folder: 입력 폴더 경로
            output_folder: 출력 폴더 경로
            file_list: 처리할 파일 목록 (None이면 전체)

        Returns:
            처리된 파일 개수
        """
        processed_count = 0

        # 파일 목록 결정
        if file_list is None:
            file_list = [f for f in os.listdir(input_folder)
                        if f.lower().endswith(('.jpg', '.jpeg'))]

        for filename in file_list:
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            if self.composite_image(input_path, output_path):
                processed_count += 1
                print(f"  ✅ {filename} 처리 완료")
            else:
                print(f"  ❌ {filename} 처리 실패")

        return processed_count
