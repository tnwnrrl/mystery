"""
4컷 레이아웃 합성 엔진
DNP DS620 6x8" 용지에 2x2 그리드로 사진 4장 배치
"""

from PIL import Image
import os


# 상수 정의 (8x6" @ 300DPI, 가로 방향)
CANVAS_WIDTH = 2400
CANVAS_HEIGHT = 1800
CELL_WIDTH = 1200
CELL_HEIGHT = 900
COLUMNS = 2
ROWS = 2
NUM_SLOTS = 4
DPI = 300


class LayoutEngine:
    """4컷 레이아웃 합성 엔진"""

    def __init__(self, fit_mode='fill'):
        """
        Args:
            fit_mode: 'fill' (셀 채우기, 크롭) 또는 'fit' (비율 유지, 여백)
        """
        self.fit_mode = fit_mode
        self.slots = [None] * NUM_SLOTS  # 4개 슬롯
        self.slot_positions = self._calculate_positions()

    def _calculate_positions(self):
        """각 슬롯의 (x, y) 위치 계산"""
        positions = []
        for row in range(ROWS):
            for col in range(COLUMNS):
                x = col * CELL_WIDTH
                y = row * CELL_HEIGHT
                positions.append((x, y))
        return positions

    def load_image(self, index, path):
        """
        슬롯에 이미지 로드

        Args:
            index: 슬롯 인덱스 (0-5)
            path: 이미지 파일 경로

        Returns:
            bool: 성공 여부
        """
        if not 0 <= index < NUM_SLOTS:
            return False

        try:
            img = Image.open(path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            self.slots[index] = img
            return True
        except Exception as e:
            print(f"이미지 로드 실패 [{index}]: {e}")
            return False

    def clear_image(self, index):
        """슬롯에서 이미지 제거"""
        if 0 <= index < NUM_SLOTS:
            if self.slots[index]:
                self.slots[index].close()
            self.slots[index] = None

    def clear_all(self):
        """모든 슬롯 비우기"""
        for i in range(NUM_SLOTS):
            self.clear_image(i)

    def set_fit_mode(self, mode):
        """fill 또는 fit 모드 설정"""
        if mode in ('fill', 'fit'):
            self.fit_mode = mode

    def _fit_image_to_cell(self, img):
        """
        이미지를 셀 크기에 맞춤

        Args:
            img: PIL Image

        Returns:
            PIL Image: 셀 크기에 맞춰진 이미지 (900x800)
        """
        img_width, img_height = img.size
        cell_ratio = CELL_WIDTH / CELL_HEIGHT
        img_ratio = img_width / img_height

        if self.fit_mode == 'fill':
            # 셀을 완전히 채움 (크롭)
            if img_ratio > cell_ratio:
                # 이미지가 더 넓음 → 높이 기준, 좌우 크롭
                new_height = CELL_HEIGHT
                new_width = int(img_width * (CELL_HEIGHT / img_height))
            else:
                # 이미지가 더 좁음 → 너비 기준, 상하 크롭
                new_width = CELL_WIDTH
                new_height = int(img_height * (CELL_WIDTH / img_width))

            resized = img.resize((new_width, new_height), Image.LANCZOS)

            # 중앙 크롭
            left = (new_width - CELL_WIDTH) // 2
            top = (new_height - CELL_HEIGHT) // 2
            cropped = resized.crop((left, top, left + CELL_WIDTH, top + CELL_HEIGHT))
            return cropped

        else:  # fit 모드
            # 비율 유지, 셀 안에 맞춤 (여백 가능)
            if img_ratio > cell_ratio:
                # 이미지가 더 넓음 → 너비 기준
                new_width = CELL_WIDTH
                new_height = int(CELL_WIDTH / img_ratio)
            else:
                # 이미지가 더 좁음 → 높이 기준
                new_height = CELL_HEIGHT
                new_width = int(CELL_HEIGHT * img_ratio)

            resized = img.resize((new_width, new_height), Image.LANCZOS)

            # 흰 배경 중앙 배치
            cell = Image.new('RGB', (CELL_WIDTH, CELL_HEIGHT), (255, 255, 255))
            x = (CELL_WIDTH - new_width) // 2
            y = (CELL_HEIGHT - new_height) // 2
            cell.paste(resized, (x, y))
            return cell

    def generate_layout(self):
        """
        6컷 레이아웃 생성

        Returns:
            PIL Image: 1800x2400 캔버스
        """
        canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), (255, 255, 255))

        for i, img in enumerate(self.slots):
            if img is None:
                continue

            fitted = self._fit_image_to_cell(img)
            x, y = self.slot_positions[i]
            canvas.paste(fitted, (x, y))

        return canvas

    def generate_preview(self, scale=0.25):
        """
        미리보기용 축소 이미지 생성

        Args:
            scale: 축소 비율 (기본 0.25 → 450x600)

        Returns:
            PIL Image: 축소된 캔버스
        """
        canvas = self.generate_layout()
        preview_size = (int(CANVAS_WIDTH * scale), int(CANVAS_HEIGHT * scale))
        return canvas.resize(preview_size, Image.LANCZOS)

    def save_layout(self, path, quality=95):
        """
        레이아웃을 JPEG로 저장 (300 DPI 메타데이터)

        Args:
            path: 저장 경로
            quality: JPEG 품질 (기본 95)

        Returns:
            bool: 성공 여부
        """
        try:
            canvas = self.generate_layout()

            # 디렉토리 생성
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)

            # 300 DPI 메타데이터와 함께 저장
            canvas.save(path, 'JPEG', quality=quality, dpi=(DPI, DPI))
            return True
        except Exception as e:
            print(f"레이아웃 저장 실패: {e}")
            return False

    def get_slot_count(self):
        """현재 로드된 이미지 개수"""
        return sum(1 for s in self.slots if s is not None)

    def is_slot_filled(self, index):
        """특정 슬롯에 이미지가 있는지 확인"""
        return 0 <= index < NUM_SLOTS and self.slots[index] is not None

    def prepare_individual_prints(self, output_dir, quality=95):
        """
        개별 사진 4장을 6x4 크기로 준비 (자동 커팅용)

        Args:
            output_dir: 임시 파일 저장 디렉토리
            quality: JPEG 품질

        Returns:
            list: 저장된 파일 경로 목록
        """
        # 6x4인치 @ 300DPI = 1800 x 1200 픽셀
        PRINT_WIDTH = 1800
        PRINT_HEIGHT = 1200

        os.makedirs(output_dir, exist_ok=True)
        saved_files = []

        for i, img in enumerate(self.slots):
            if img is None:
                continue

            # 6x4 크기로 리사이즈 (fill 모드)
            img_width, img_height = img.size
            target_ratio = PRINT_WIDTH / PRINT_HEIGHT
            img_ratio = img_width / img_height

            if img_ratio > target_ratio:
                # 이미지가 더 넓음 → 높이 기준
                new_height = PRINT_HEIGHT
                new_width = int(img_width * (PRINT_HEIGHT / img_height))
            else:
                # 이미지가 더 좁음 → 너비 기준
                new_width = PRINT_WIDTH
                new_height = int(img_height * (PRINT_WIDTH / img_width))

            resized = img.resize((new_width, new_height), Image.LANCZOS)

            # 중앙 크롭
            left = (new_width - PRINT_WIDTH) // 2
            top = (new_height - PRINT_HEIGHT) // 2
            cropped = resized.crop((left, top, left + PRINT_WIDTH, top + PRINT_HEIGHT))

            # 저장
            file_path = os.path.join(output_dir, f"print_{i+1}.jpg")
            cropped.save(file_path, 'JPEG', quality=quality, dpi=(DPI, DPI))
            saved_files.append(file_path)

        return saved_files
