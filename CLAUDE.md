# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

대본 기반 TTS 프로그램 - 펑션키(F1~F10)로 미리 설정된 대사를 재생하고, 직접 한글 입력도 가능한 자막 시스템. 보조 모니터가 있으면 자동으로 보조 모니터에서 전체화면 실행.

## 실행 및 배포

```bash
# 로컬 실행
python3.12 main.py

# Mac mini 원격 배포 (한 줄)
sshpass -p '1111' scp main.py scripts.json kim@192.168.0.24:~/ && \
sshpass -p '1111' ssh kim@192.168.0.24 'pkill -f "python3.12 main.py"; osascript -e "tell application \"Terminal\" to do script \"cd ~ && /usr/local/bin/python3.12 main.py\""'
```

**주의**: Mac mini에서는 `/usr/local/bin/python3.12` 전체 경로 필수 (PATH 미설정)

## 주요 제약사항

- **macOS 전용**: `say` 명령어와 Yuna 음성 사용
- **Python 3.12 필요**: 원격 Mac에서 tkinter 호환성 문제로 3.12 사용
- **오프라인 작동**: 인터넷 연결 불필요
- **보조 모니터 배치**: 메인 모니터 오른쪽에 있다고 가정

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

## 아키텍처

```
get_secondary_monitor()     # system_profiler로 보조 모니터 감지
                            # 메인 오른쪽 모니터 좌표 반환

KoreanTTSApp
├── load_scripts()          # scripts.json에서 대본 로드
├── split_sentences()       # 문장 분리 (마침표/물음표/느낌표)
├── tts_queue + tts_worker  # 백그라운드 TTS 스레드
├── play_script()           # 대본을 문장 단위로 큐에 추가
├── on_previous/next_sentence()  # 문장/F키 간 탐색
├── stop_playback()         # 재생 중지 (큐 비우기 + 프로세스 종료)
└── hidden_entry            # 한글 IME 입력용 숨겨진 위젯
```

## 대본 수정

`scripts.json` 파일에서 직접 수정 (코드 수정 불필요):
```json
{
    "F1": "첫 번째 대사. 두 번째 문장.",
    "F2": "..."
}
```

## 음성 변경

`play_tts()` 메서드의 `-v` 옵션 수정:
```python
# 사용 가능한 한국어 음성: Yuna, Eddy, Flo, Grandma, Grandpa, Reed, Rocko, Sandy, Shelley
'-v', 'Yuna'
```

## 원격 장치 정보

[ssh.md](ssh.md) 참조 - Mac mini (192.168.0.24), Raspberry Pi (192.168.0.28), Home Assistant (192.168.0.100)
