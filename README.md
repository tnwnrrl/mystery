# ◢ REVERSE AUDIO ANALYZER ◣

사이버펑크 스타일의 음성 역재생 프로그램

## 기능

- **오디오 파일 로드**: MP3, WAV 파일 지원
- **역재생**: 오디오를 거꾸로 재생
- **속도 조절**: 0.5x ~ 2.0x 배속 조절 가능
- **파형 시각화**: 실시간 오디오 파형 표시
- **스펙트럼 분석기**: 주파수 스펙트럼 분석 및 시각화
- **기술 정보 표시**: 샘플레이트, 비트레이트, 채널, 비트 깊이 등

## 설치 방법

```bash
cd reverse_audio_player
pip install -r requirements.txt
```

## 실행 방법

```bash
python main.py
```

## 사용법

1. **파일 로드**: "◢ LOAD AUDIO FILE ◣" 버튼을 눌러 MP3 또는 WAV 파일 선택
2. **역재생 처리**: "◢ REVERSE AUDIO ◣" 버튼을 눌러 오디오 역재생 처리
3. **재생**: "▶ PLAY" 버튼으로 역재생된 오디오 재생
4. **속도 조절**: "SPEED MULTIPLIER" 슬라이더로 재생 속도 조절
5. **일시정지/정지**: "▮▮ PAUSE" 또는 "■ STOP" 버튼 사용

## 시각화

- **WAVEFORM ANALYSIS**: 오디오 파형을 시각적으로 표시
- **FREQUENCY SPECTRUM**: 주파수 대역별 강도를 막대 그래프로 표시
- **TECHNICAL METRICS**: 오디오 파일의 기술적 정보 표시

## 요구사항

- Python 3.7+
- pygame
- numpy
- pydub
- matplotlib
- pillow

## 특징

- 🎨 사이버펑크 다크 테마 UI
- 📊 실시간 파형 및 스펙트럼 시각화
- ⚡ 빠른 오디오 처리
- 🎧 고품질 오디오 재생
- 📈 기술적 메트릭 표시

---
**◢ REVERSE AUDIO ANALYZER v2.0 ◣**
