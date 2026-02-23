# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DNP DS620 4컷 레이아웃 앱. 5x7" 용지에 2x2 그리드로 사진 4장 배치. 절반 커팅하여 5x3.5" 카드 2장 출력. tkinter GUI 제공.

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
print(f'캔버스: {engine.generate_layout().size}')  # (1500, 2100)
"

# 의존성 설치
pip install -r requirements.txt
```

## Architecture

```
이미지 선택/폴더 로드
    ↓
LayoutEngine.load_image(index, path)
    ↓ 슬롯 0-3에 저장
    ↓
[4장 미만?] → _auto_fill_empty_slots() → 마지막 사진으로 채움
    ↓
LayoutEngine._fit_image_to_cell(img)
    ↓ fill (크롭) 또는 fit (여백) 모드
    ↓
LayoutEngine.generate_layout()
    ↓ 1500x2100 캔버스에 합성
    ↓
LayoutEngine.prepare_half_prints()
    ↓ 상단(1500x1050) + 하단(1500x1050) 분할
    ↓
MacPrinter.print_individual_photos(paths)
    ↓ dnp3.5x5 × 2장 → 5x7 용지 1장, 절반 커팅
```

### 픽셀 계산 (5x7" @ 300DPI, 세로)

```
전체 캔버스: 1500 x 2100 pixels
셀 크기: 750 x 1050 pixels

       5" (1500px)
┌──────────┬──────────┐ ─┐
│  슬롯0   │  슬롯1   │  │ 3.5" (1050px)
╞══════════╪══════════╡ ─┤ ✂️ 커팅
│  슬롯2   │  슬롯3   │  │ 3.5" (1050px)
└──────────┴──────────┘ ─┘
  2.5"        2.5"
```

### Core Files

| 파일 | 역할 |
|------|------|
| `gui.py` | 메인 진입점. tkinter GUI, 자동 채우기 기능 |
| `utils/layout_engine.py` | `LayoutEngine` - 4컷 합성 엔진, 절반 분할 |
| `utils/printer.py` | `MacPrinter` - macOS 프린터 연동 (dnp3.5x5) |

## Fit Modes

| 모드 | 설명 |
|------|------|
| `fill` | 셀을 완전히 채움 (이미지 일부 크롭) |
| `fit` | 비율 유지 (흰 여백 발생 가능) |

## Key Constraints

- **macOS only**: `open -a Preview` 및 `lpstat` 명령 사용
- **JPG 출력**: 300 DPI 메타데이터 포함
- **5x7" 전용**: DNP DS620 5x7" 용지 기준 설계
- **절반 커팅**: 5x3.5" 카드 2장 출력
- **Pillow 필수**: 이미지 처리에 PIL 사용
