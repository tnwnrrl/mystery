# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

한글 입력 TTS 프로그램 - 키보드로 한글을 입력하면 실시간으로 화면에 자막이 표시되고, Enter를 누르면 음성으로 재생됩니다.

## 실행 방법

```bash
./run.sh
# 또는
python3 main.py
```

## 주요 제약사항

- **macOS 전용**: `say` 명령어와 Yuna 음성 사용
- **오프라인 작동**: 인터넷 연결 불필요
- **한글 IME**: tkinter Entry 위젯으로 한글 조합 처리

## 아키텍처

단일 파일 구조 (`main.py`):
- `KoreanTTSApp`: 메인 애플리케이션 클래스
  - 숨겨진 Entry 위젯으로 한글 IME 입력 캡처
  - 백그라운드 스레드에서 TTS 큐 처리
  - `sent_text`로 이미 재생된 텍스트와 새 입력 구분

## 음성 변경

다른 한국어 음성 사용 시 `play_tts()` 메서드의 `-v` 옵션 수정:
```python
# 사용 가능한 한국어 음성: Yuna, Eddy, Flo, Grandma, Grandpa, Reed, Rocko, Sandy, Shelley
'-v', 'Yuna'
```
