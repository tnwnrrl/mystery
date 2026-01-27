# Mystery - 방탈출 체험존 통합 시스템

4개 프로젝트의 모노레포

## Modules

| 모듈 | 설명 |
|------|------|
| [old_tv](old_tv/) | RPi + ESP32 MQTT 멀티미디어 |
| [photo](photo/) | Canon 100D 카메라 모니터링 |
| [photo_layout](photo_layout/) | DNP DS620 6컷 레이아웃 인쇄 |
| [reserve](reserve/) | Reverse Audio Analyzer |

## Installation

```bash
pip install -r requirements.txt

# macOS only
brew install libgphoto2 pkg-config ffmpeg
```

## Documentation

각 모듈의 상세 문서는 해당 디렉토리의 `CLAUDE.md` 참조.
