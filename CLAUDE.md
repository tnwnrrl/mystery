# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

DNP DS620 6컷 레이아웃 앱. 6x8" 용지에 2x3 그리드로 사진 6장 배치. tkinter GUI 제공.

## Commands

```bash
# 앱 실행 (권장)
./start.command

# 수동 GUI 실행
python3 gui.py

# 레이아웃 엔진 테스트
python3 -c "
from utils.layout_engine import LayoutEngine
engine = LayoutEngine()
layout = engine.generate_layout()
print(f'캔버스 크기: {layout.size}')  # (1800, 2400)
"

# 프린터 목록 확인
python3 -c "
from utils.printer import MacPrinter
printer = MacPrinter()
print(printer.list_printers())
"

# 의존성 설치
pip install -r requirements.txt
```

## Architecture

```
사용자 이미지 선택
    ↓
LayoutEngine.load_image(index, path)
    ↓ 슬롯 0-5에 저장
    ↓
LayoutEngine._fit_image_to_cell(img)
    ↓ fill (크롭) 또는 fit (여백) 모드
    ↓
LayoutEngine.generate_layout()
    ↓ 1800x2400 캔버스에 합성
    ↓
LayoutEngine.save_layout(path)
    ↓ JPEG 300 DPI
    ↓
MacPrinter.print_image_directly(path)
    ↓ Preview 앱으로 열기
인쇄
```

### 픽셀 계산 (6x8" @ 300DPI)

```
전체 캔버스: 1800 x 2400 pixels
그리드: 2열 x 3행
셀 크기: 900 x 800 pixels

┌─────────┬─────────┐
│ 슬롯0   │ 슬롯1   │  y=0
├─────────┼─────────┤
│ 슬롯2   │ 슬롯3   │  y=800
├─────────┼─────────┤
│ 슬롯4   │ 슬롯5   │  y=1600
└─────────┴─────────┘
  x=0       x=900
```

### Core Files

| 파일 | 역할 |
|------|------|
| `gui.py` | 메인 진입점. tkinter GUI |
| `utils/layout_engine.py` | `LayoutEngine` - 6컷 합성 엔진 |
| `utils/printer.py` | `MacPrinter` - macOS 프린터 연동 |
| `config.json` | 설정 (캔버스 크기, DPI, 출력 폴더) |

## Fit Modes

| 모드 | 설명 | 결과 |
|------|------|------|
| `fill` | 셀을 완전히 채움 | 이미지 일부 크롭 |
| `fit` | 비율 유지 | 흰 여백 발생 가능 |

## Key Constraints

- **macOS only**: `open -a Preview` 및 `lpstat` 명령 사용
- **JPG 출력**: 300 DPI 메타데이터 포함
- **6x8" 전용**: DNP DS620 6x8" 용지 기준 설계
- **Pillow 필수**: 이미지 처리에 PIL 사용
