# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

라즈베리파이 기반 영상 재생 시스템 (old_TV)

## Raspberry Pi Access

```bash
# SSH 접속
sshpass -p '1' ssh pi@172.20.10.2

# 파일 업로드
sshpass -p '1' scp <local_file> pi@172.20.10.2:~/

# 접속 정보는 raspberry_pi.env 참조
```

## Remote Scripts (on Raspberry Pi)

| 경로 | 설명 |
|------|------|
| `~/play_video.py` | VLC 기반 전체화면 반복 재생 |
| `~/videos/` | 영상 파일 저장 폴더 |

## Commands

```bash
# 영상 재생 (라즈베리파이에서)
python3 ~/play_video.py

# 영상 업로드 (로컬에서)
sshpass -p '1' scp videos/1.mp4 pi@172.20.10.2:~/videos/
```

## Hardware Specs

- Display: 1280x720 (HD)
- OS: Linux 6.12.47 (aarch64)
- Python: 3.13.5
- Video Player: VLC
