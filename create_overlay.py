#!/usr/bin/env python3
"""
테스트용 오버레이 PNG 생성 스크립트
반투명 워터마크 스타일의 샘플 오버레이 생성
"""

from PIL import Image, ImageDraw, ImageFont

# 1920 x 1080 (Full HD)
width = 1920
height = 1080

# RGBA 이미지 생성 (투명 배경)
overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

# 반투명 테두리 추가 (장식용)
border_width = 20
border_color = (255, 255, 255, 100)  # 흰색, 약간 투명

# 상단 테두리
draw.rectangle(
    [(0, 0), (width, border_width)],
    fill=border_color
)

# 하단 테두리
draw.rectangle(
    [(0, height - border_width), (width, height)],
    fill=border_color
)

# 우하단에 워터마크 텍스트
try:
    # 시스템 폰트 사용
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 50)
except:
    # 기본 폰트 사용
    font = ImageFont.load_default()

text = "Canon 100D"
text_color = (255, 255, 255, 150)  # 흰색, 반투명

# 텍스트 위치 (우하단)
text_bbox = draw.textbbox((0, 0), text, font=font)
text_width = text_bbox[2] - text_bbox[0]
text_height = text_bbox[3] - text_bbox[1]

text_position = (width - text_width - 40, height - text_height - 40)
draw.text(text_position, text, fill=text_color, font=font)

# 저장
overlay.save('overlay.png', 'PNG')
print("✅ overlay.png 생성 완료!")
print(f"   크기: {width} x {height}")
print("   내용: 상하단 반투명 테두리 + 우하단 워터마크")
