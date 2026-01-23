# SSH 배포 정보

## 배포 대상

| 장치 | IP | 사용자 | 비밀번호 | 경로 |
|------|-----|--------|----------|------|
| Mac mini | 192.168.0.24 | kim | 1111 | ~/photo-layout |

## 배포 명령어

```bash
# SSH 접속
sshpass -p '1111' ssh kim@192.168.0.24

# 전체 배포 (프로젝트 루트에서 실행)
sshpass -p '1111' ssh kim@192.168.0.24 'mkdir -p ~/photo-layout/utils ~/photo-layout/output'
sshpass -p '1111' scp gui.py requirements.txt kim@192.168.0.24:~/photo-layout/
sshpass -p '1111' scp utils/*.py kim@192.168.0.24:~/photo-layout/utils/
sshpass -p '1111' scp start.command kim@192.168.0.24:~/photo-layout/
```

## 바탕화면 실행

```bash
# 바탕화면에 심볼릭 링크 생성 (이미 생성됨)
sshpass -p '1111' ssh kim@192.168.0.24 'ln -sf ~/photo-layout/start.command ~/Desktop/"Photo Layout.command"'
```

## 원격 실행

```bash
# 레이아웃 엔진 테스트
sshpass -p '1111' ssh kim@192.168.0.24 'cd ~/photo-layout && python3 -c "from utils.layout_engine import LayoutEngine; print(LayoutEngine().generate_layout().size)"'

# GUI 실행 (원격에서 직접 실행 불가 - 바탕화면에서 더블클릭)
```

## 파일 구조

```
~/photo-layout/
├── gui.py              # 메인 GUI
├── start.command       # 실행 스크립트
├── requirements.txt    # 의존성
├── output/             # 저장 폴더
└── utils/
    ├── __init__.py
    ├── layout_engine.py
    └── printer.py

~/Desktop/
└── Photo Layout.command -> ~/photo-layout/start.command
```

## 참고

- Pillow는 맥미니에 전역 설치됨 (11.3.0)
- Python 3.9.6 (시스템 기본)
- 바탕화면의 "Photo Layout.command" 더블클릭으로 실행
