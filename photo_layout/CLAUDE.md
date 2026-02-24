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
    ↓ EXIF 회전 + 가로→세로 자동 회전
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
    ↓ PPD 크기(1548x1088)로 리사이즈
    ↓
MacPrinter.print_individual_photos(paths)
    ↓ dnp5x3.5 × 2장, fit-to-page, Cutter=Normal
```

### 픽셀 계산 (5x7" @ 300DPI, 세로)

```
전체 캔버스: 1500 x 2100 pixels

       5" (1500px)
       ├─80px─┤
┌──────┬──────────┬──┬──────────┐ ─┐
│여백  │  슬롯0   │  │  슬롯1   │  │ 3.5" (1050px)
│ 80px │ (695px)  │30│ (695px)  │  │
╞══════╪══════════╪══╪══════════╡ ─┤ ✂️ 커팅
│여백  │  슬롯2   │  │  슬롯3   │  │ 3.5" (1050px)
│ 80px │ (695px)  │30│ (695px)  │  │
└──────┴──────────┴──┴──────────┘ ─┘
```

### 프린터 오프셋 보정 (layout_engine.py)

DNP DS620이 왼쪽/하단에 여백을 생성하므로 소프트웨어에서 보정:

| 상수 | 값 | 용도 |
|------|-----|------|
| `PRINTER_MARGIN` | 80px | 왼쪽 여백 보정 |
| `COLUMN_GAP` | 30px | 열 간격 (하단 여백 대응) |
| `CELL_WIDTH` | 695px | `(1500 - 80 - 30) // 2` |
| `CELL_HEIGHT` | 1050px | `2100 // 2` |

이 값들은 인쇄 결과에 따라 조절 필요. `prepare_half_prints()`에서 PPD 실제 크기(1548x1088px)로 리사이즈하여 CUPS 스케일링 방지.

### Core Files

| 파일 | 역할 |
|------|------|
| `gui.py` | 메인 진입점. tkinter GUI, 미리보기(Label+ImageDraw), 자동 채우기 |
| `utils/layout_engine.py` | `LayoutEngine` - 4컷 합성 엔진, 프린터 오프셋 보정, 절반 분할 |
| `utils/printer.py` | `MacPrinter` - macOS lp/lpstat 프린터 연동 (dnp5x3.5) |

### 인쇄 파이프라인

1. `generate_layout()` → 1500x2100 캔버스 생성
2. `prepare_half_prints()` → 상/하 절반 크롭 → PPD 크기(1548x1088) 리사이즈 → JPEG 저장
3. `print_individual_photos()` → `lp -d Dai_Nippon_Printing_DP_DS620 -o PageSize=dnp5x3.5 -o Cutter=Normal -o fit-to-page`

## Fit Modes

| 모드 | 설명 |
|------|------|
| `fill` | 셀을 완전히 채움 (이미지 일부 크롭) |
| `fit` | 비율 유지 (흰 여백 발생 가능) |

## Mac mini 배포

```bash
# 파일 배포
sshpass -p '1111' scp gui.py kim@192.168.0.24:~/photo-layout/
sshpass -p '1111' scp utils/layout_engine.py kim@192.168.0.24:~/photo-layout/utils/

# 캐시 삭제 + 앱 재시작
sshpass -p '1111' ssh kim@192.168.0.24 "rm -rf ~/photo-layout/utils/__pycache__ && pkill -f 'python3 gui.py' 2>/dev/null; sleep 1; open -a Terminal ~/photo-layout/start.command"
```

배포 후 반드시 `__pycache__` 삭제할 것. 안 하면 이전 코드가 실행됨.

## Key Constraints

- **macOS only**: `lp`, `lpstat`, `open -a Preview` 명령 사용
- **JPG 출력**: 300 DPI 메타데이터 포함
- **5x7" 전용**: DNP DS620 5x7" 용지 기준 설계
- **절반 커팅**: 5x3.5" 카드 2장 출력 (dnp5x3.5 PageSize)
- **Pillow 필수**: 이미지 처리에 PIL 사용
- **PPD 크기**: dnp5x3.5 = 371.52×261.12pt = 1548×1088px @300DPI
