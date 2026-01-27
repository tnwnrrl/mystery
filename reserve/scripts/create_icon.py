#!/usr/bin/env python3
"""
앱 아이콘 생성 스크립트 (오실로스코프 스타일)
"""

import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
import math

def create_oscilloscope_icon(size=1024):
    """오실로스코프 스타일 아이콘 생성"""

    # 검정 배경
    img = Image.new('RGBA', (size, size), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # 외곽 테두리 (둥근 모서리)
    margin = size // 16
    corner_radius = size // 8

    # 외곽선 (진한 녹색)
    border_color = (0, 26, 0, 255)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=corner_radius,
        outline=(0, 170, 0, 255),
        width=size // 50
    )

    # 내부 영역
    inner_margin = margin + size // 20
    draw.rounded_rectangle(
        [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
        radius=corner_radius // 2,
        fill=(10, 10, 10, 255),
        outline=(0, 26, 0, 255),
        width=size // 80
    )

    # 그리드 라인
    grid_area = (inner_margin + size // 25, inner_margin + size // 25,
                 size - inner_margin - size // 25, size - inner_margin - size // 25)
    grid_color = (0, 26, 0, 200)

    # 수평 그리드
    for i in range(5):
        y = grid_area[1] + (grid_area[3] - grid_area[1]) * i / 4
        draw.line([(grid_area[0], y), (grid_area[2], y)], fill=grid_color, width=size // 200)

    # 수직 그리드
    for i in range(5):
        x = grid_area[0] + (grid_area[2] - grid_area[0]) * i / 4
        draw.line([(x, grid_area[1]), (x, grid_area[3])], fill=grid_color, width=size // 200)

    # 파형 그리기 (역재생 심볼: 뒤집힌 사인파)
    wave_points = []
    wave_center_y = (grid_area[1] + grid_area[3]) / 2
    wave_amplitude = (grid_area[3] - grid_area[1]) * 0.35

    for i in range(100):
        x = grid_area[0] + (grid_area[2] - grid_area[0]) * i / 99
        # 역재생 느낌의 파형 (감쇠된 사인파, 뒤집힌 방향)
        t = i / 99 * 4 * math.pi
        y = wave_center_y - wave_amplitude * math.sin(-t) * (1 - i / 150)
        wave_points.append((x, y))

    # 파형 글로우 효과
    for glow_width, alpha in [(size // 40, 80), (size // 60, 150), (size // 100, 255)]:
        glow_color = (0, 255, 65, alpha)
        if len(wave_points) > 1:
            draw.line(wave_points, fill=glow_color, width=glow_width)

    # 역재생 심볼 (왼쪽 화살표)
    arrow_size = size // 8
    arrow_x = size // 2 - arrow_size // 2
    arrow_y = size - inner_margin - arrow_size - size // 30

    arrow_points = [
        (arrow_x, arrow_y + arrow_size // 2),                    # 왼쪽 꼭지점
        (arrow_x + arrow_size * 0.7, arrow_y),                   # 오른쪽 위
        (arrow_x + arrow_size * 0.7, arrow_y + arrow_size // 3), # 오른쪽 위 안쪽
        (arrow_x + arrow_size, arrow_y + arrow_size // 3),       # 맨 오른쪽 위
        (arrow_x + arrow_size, arrow_y + arrow_size * 2 // 3),   # 맨 오른쪽 아래
        (arrow_x + arrow_size * 0.7, arrow_y + arrow_size * 2 // 3), # 오른쪽 아래 안쪽
        (arrow_x + arrow_size * 0.7, arrow_y + arrow_size),      # 오른쪽 아래
    ]
    draw.polygon(arrow_points, fill=(0, 255, 65, 255))

    return img


def create_iconset(base_image, output_dir):
    """다양한 크기의 아이콘셋 생성"""

    iconset_dir = os.path.join(output_dir, 'AppIcon.iconset')
    os.makedirs(iconset_dir, exist_ok=True)

    # macOS가 요구하는 아이콘 크기들
    sizes = [
        (16, '16x16'),
        (32, '16x16@2x'),
        (32, '32x32'),
        (64, '32x32@2x'),
        (128, '128x128'),
        (256, '128x128@2x'),
        (256, '256x256'),
        (512, '256x256@2x'),
        (512, '512x512'),
        (1024, '512x512@2x'),
    ]

    for size, name in sizes:
        resized = base_image.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(os.path.join(iconset_dir, f'icon_{name}.png'))

    return iconset_dir


def create_icns(iconset_dir, output_path):
    """iconset을 icns로 변환"""
    try:
        subprocess.run([
            'iconutil', '-c', 'icns', iconset_dir, '-o', output_path
        ], check=True)
        print(f"아이콘 생성 완료: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"iconutil 실행 실패: {e}")
        return False
    except FileNotFoundError:
        print("iconutil을 찾을 수 없습니다 (macOS 전용)")
        return False


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)

    # 아이콘 생성
    print("오실로스코프 아이콘 생성 중...")
    icon_image = create_oscilloscope_icon(1024)

    # PNG로도 저장 (미리보기용)
    png_path = os.path.join(project_dir, 'AppIcon.png')
    icon_image.save(png_path)
    print(f"PNG 저장: {png_path}")

    # iconset 생성
    print("iconset 생성 중...")
    iconset_dir = create_iconset(icon_image, project_dir)

    # icns 생성
    icns_path = os.path.join(project_dir, 'AppIcon.icns')
    if create_icns(iconset_dir, icns_path):
        # 정리
        import shutil
        shutil.rmtree(iconset_dir)
        print("완료!")
    else:
        print(f"iconset 유지: {iconset_dir}")
        print("수동으로 icns 변환이 필요합니다")


if __name__ == '__main__':
    main()
