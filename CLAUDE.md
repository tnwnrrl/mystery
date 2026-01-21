# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

대본 기반 TTS 프로그램 - 펑션키(F1~F10)로 미리 설정된 대사를 재생하고, 직접 한글 입력도 가능한 자막 시스템

## 실행 방법

```bash
python3.12 main.py
# 또는
./run.sh
```

**원격 Mac 배포**: [ssh.md](ssh.md) 참조
```bash
sshpass -p '1111' scp main.py scripts.json kim@192.168.0.24:~/
sshpass -p '1111' ssh kim@192.168.0.24 'osascript -e "tell application \"Terminal\" to do script \"python3.12 main.py\""'
```

## 주요 제약사항

- **macOS 전용**: `say` 명령어와 Yuna 음성 사용
- **Python 3.12 필요**: 원격 Mac에서 tkinter 호환성 문제로 3.12 사용
- **오프라인 작동**: 인터넷 연결 불필요

## 조작법

| 키 | 기능 |
|---|---|
| F1~F10 | 대본 재생 |
| 같은 키 재누름 | 즉시 중지 |
| 다른 키 누름 | 전환 재생 |
| ← | 이전 문장 (첫 문장에서 누르면 이전 F키로 이동) |
| → | 다음 문장 (마지막 문장에서 누르면 다음 F키로 이동) |
| Enter | 직접 입력 텍스트 재생 |
| ESC | 종료 |

## 파일 구조

```
tts test/
├── main.py          # 메인 애플리케이션
├── scripts.json     # 대본 파일 (F1~F10)
├── ssh.md           # SSH 접속 정보 (장치별)
├── CLAUDE.md        # 프로젝트 문서
├── requirements.txt # 의존성
└── run.sh           # 실행 스크립트
```

## 아키텍처

```
KoreanTTSApp
├── scripts.json         # 외부 대본 파일
├── load_scripts()       # JSON에서 대본 로드
├── split_sentences()    # 문장 분리 (마침표/물음표/느낌표)
├── tts_queue            # TTS 재생 큐
├── tts_worker()         # 백그라운드 TTS 스레드
├── play_script()        # 대본을 문장 단위로 분리 후 큐에 추가
├── on_previous/next_sentence()  # 문장/F키 간 탐색
├── stop_playback()      # 재생 중지 (큐 비우기 + 프로세스 종료)
└── hidden_entry         # 한글 IME 입력용 숨겨진 위젯
```

## 대본 수정

`scripts.json` 파일에서 직접 수정 (코드 수정 불필요):
```json
{
    "F1": "첫 번째 대사. 두 번째 문장.",
    "F2": "...",
    "F3": "..."
}
```

## 음성 변경

`play_tts()` 메서드의 `-v` 옵션 수정:
```python
# 사용 가능한 한국어 음성: Yuna, Eddy, Flo, Grandma, Grandpa, Reed, Rocko, Sandy, Shelley
'-v', 'Yuna'
```
