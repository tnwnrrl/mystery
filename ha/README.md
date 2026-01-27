# Home Assistant 설정

## 자동화 적용

```bash
# HA SSH 접속
sshpass -p 'qwerqwer' ssh mystery@192.168.0.100

# 자동화 복사 (기존 파일에 추가)
cat ha/automations/old_tv.yaml >> /homeassistant/automations.yaml

# 또는 전체 교체
scp ha/automations/old_tv.yaml mystery@192.168.0.100:/homeassistant/automations.yaml

# HA 재시작
# HA 웹 UI → 개발자 도구 → 자동화 다시 불러오기
```

## input_number 헬퍼 (필수)

HA UI 또는 configuration.yaml에 추가:

```yaml
input_number:
  scene_state:
    name: "현재 씬 번호"
    min: 0
    max: 5
    step: 1
    initial: 0
```

## MQTT 브로커

- **호스트**: 192.168.0.100
- **사용자**: mystery
- **비밀번호**: qwerqwer

## 관련 장치

- IKEA RODRET (91afeecd96c2793ecdfebd81c5e5bc11) - 씬 0-3
- IKEA RODRET (40d8a5e1c093a93e6206baf6d0e29fea) - 씬 4-5
- switch.doll - 인형 조명
- switch.monkey - 원숭이 조명
- light.light1, light.light2 - 조명
