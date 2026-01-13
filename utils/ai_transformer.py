"""
AI 이미지 변환 모듈 (Gemini 2.5 Flash Image)

하이브리드 모드:
- 온라인: AI 변환
- 오프라인: 오버레이 합성 폴백

requests 기반 직접 API 호출 (google-genai SDK 미사용)
- pydantic 의존성 제거
- macOS 버전 호환성 문제 해결
"""

import os
import socket
import base64
import json
from typing import Optional, Tuple

import requests
from PIL import Image


def check_internet(host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> bool:
    """인터넷 연결 확인 (DNS 서버 접근)"""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except (socket.error, OSError):
        return False


class AITransformer:
    """AI 이미지 변환 클래스 (Gemini API - requests 직접 호출)"""

    API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, config: dict):
        """
        Args:
            config: AI 설정 딕셔너리
                - api_key: Gemini API 키
                - model: 모델명 (기본: gemini-2.0-flash-exp)
                - prompt: 변환 프롬프트
                - timeout_seconds: 타임아웃 (기본: 120)
        """
        self.api_key = config.get('api_key', '')
        self.model = config.get('model', 'gemini-2.0-flash-exp')
        self.prompt = config.get('prompt', '')
        self.timeout = config.get('timeout_seconds', 120)

        if self.api_key:
            print(f"✅ AI 클라이언트 초기화 완료 (모델: {self.model})")
        else:
            print("⚠️ AI API 키가 설정되지 않았습니다.")

    def is_available(self) -> Tuple[bool, str]:
        """
        AI 변환 가능 여부 확인

        Returns:
            (가능 여부, 사유 메시지)
        """
        if not self.api_key:
            return False, "API 키 미설정"

        if not self.prompt:
            return False, "프롬프트 미설정"

        if not check_internet():
            return False, "인터넷 연결 없음"

        return True, "준비됨"

    def _encode_image(self, image_path: str) -> Tuple[str, str]:
        """이미지를 base64로 인코딩"""
        with open(image_path, "rb") as f:
            data = f.read()

        # MIME 타입 결정
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')

        return base64.b64encode(data).decode('utf-8'), mime_type

    def transform_image(self, input_path: str, output_path: str) -> Tuple[bool, str]:
        """
        이미지를 AI로 변환

        Args:
            input_path: 입력 이미지 경로
            output_path: 출력 이미지 경로

        Returns:
            (성공 여부, 결과 메시지)
        """
        # 사전 검증
        available, reason = self.is_available()
        if not available:
            return False, f"AI 변환 불가: {reason}"

        try:
            # 이미지 base64 인코딩
            image_data, mime_type = self._encode_image(input_path)

            # API 요청 구성
            url = f"{self.API_BASE}/{self.model}:generateContent?key={self.api_key}"

            payload = {
                "contents": [{
                    "parts": [
                        {"text": self.prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "responseModalities": ["TEXT", "IMAGE"]
                }
            }

            headers = {
                "Content-Type": "application/json"
            }

            # API 호출
            print(f"🔄 AI 변환 중... (타임아웃: {self.timeout}초)")
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            # 응답 처리
            if response.status_code != 200:
                error_detail = response.text[:200]
                if response.status_code == 401:
                    return False, "API 키 인증 실패"
                elif response.status_code == 429:
                    return False, "API 할당량 초과"
                elif response.status_code == 400:
                    return False, f"잘못된 요청: {error_detail}"
                else:
                    return False, f"API 오류 ({response.status_code}): {error_detail}"

            result = response.json()

            # 응답에서 이미지 추출
            candidates = result.get('candidates', [])
            for candidate in candidates:
                content = candidate.get('content', {})
                parts = content.get('parts', [])

                for part in parts:
                    inline_data = part.get('inlineData')
                    if inline_data:
                        # 이미지 데이터 추출
                        image_bytes = base64.b64decode(inline_data['data'])

                        # 출력 폴더 생성
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)

                        # 이미지 저장
                        with open(output_path, "wb") as f:
                            f.write(image_bytes)

                        return True, "AI 변환 완료"

            return False, "API 응답에 이미지 없음"

        except requests.exceptions.Timeout:
            return False, f"API 타임아웃 ({self.timeout}초)"
        except requests.exceptions.ConnectionError:
            return False, "네트워크 연결 오류"
        except Exception as e:
            return False, f"AI 변환 실패: {str(e)}"

    def update_prompt(self, new_prompt: str):
        """프롬프트 업데이트"""
        self.prompt = new_prompt

    def update_api_key(self, new_key: str):
        """API 키 업데이트"""
        self.api_key = new_key
        if new_key:
            print(f"✅ API 키 업데이트 완료")


class HybridProcessor:
    """하이브리드 이미지 처리기 (AI + 오버레이 폴백)"""

    def __init__(self, config: dict):
        """
        Args:
            config: 전체 설정 딕셔너리
        """
        self.config = config
        self.ai_transformer = None
        self.image_processor = None
        self.mode = config.get('processing', {}).get('mode', 'hybrid')  # ai, overlay, hybrid

        self._init_processors()

    def _init_processors(self):
        """프로세서 초기화"""
        # AI 변환기 초기화
        ai_config = self.config.get('ai', {})
        if ai_config.get('api_key'):
            self.ai_transformer = AITransformer(ai_config)

        # 오버레이 프로세서 초기화 (폴백용)
        from utils.image_processor import ImageProcessor
        overlay_path = self.config.get('paths', {}).get('overlay_image', '')
        if overlay_path and os.path.exists(overlay_path):
            self.image_processor = ImageProcessor(overlay_path)

    def process_image(self, input_path: str, output_path: str) -> Tuple[bool, str, str]:
        """
        이미지 처리 (하이브리드)

        Args:
            input_path: 입력 이미지 경로
            output_path: 출력 이미지 경로

        Returns:
            (성공 여부, 사용된 방식, 결과 메시지)
        """
        # AI 전용 모드
        if self.mode == 'ai':
            if self.ai_transformer:
                success, msg = self.ai_transformer.transform_image(input_path, output_path)
                return success, 'ai', msg
            else:
                return False, 'ai', "AI 변환기 미설정"

        # 오버레이 전용 모드
        if self.mode == 'overlay':
            if self.image_processor:
                success = self.image_processor.composite_image(input_path, output_path)
                return success, 'overlay', "오버레이 합성 완료" if success else "오버레이 합성 실패"
            else:
                return False, 'overlay', "오버레이 프로세서 미설정"

        # 하이브리드 모드: AI 우선, 실패 시 오버레이 폴백
        if self.ai_transformer:
            success, msg = self.ai_transformer.transform_image(input_path, output_path)
            if success:
                return True, 'ai', msg

            # AI 실패 시 폴백
            print(f"⚠️ AI 변환 실패 ({msg}), 오버레이 폴백 시도...")

        # 오버레이 폴백
        if self.image_processor:
            success = self.image_processor.composite_image(input_path, output_path)
            if success:
                return True, 'overlay', "오버레이 폴백 사용"
            else:
                return False, 'overlay', "오버레이 폴백도 실패"

        return False, 'none', "처리 가능한 방식 없음"

    def get_status(self) -> dict:
        """현재 상태 반환"""
        status = {
            'mode': self.mode,
            'ai_available': False,
            'ai_reason': '',
            'overlay_available': False
        }

        if self.ai_transformer:
            status['ai_available'], status['ai_reason'] = self.ai_transformer.is_available()
        else:
            status['ai_reason'] = "AI 변환기 미설정"

        status['overlay_available'] = self.image_processor is not None and \
                                       self.image_processor.overlay_image is not None

        return status

    def set_mode(self, mode: str):
        """처리 모드 설정 (ai, overlay, hybrid)"""
        if mode in ('ai', 'overlay', 'hybrid'):
            self.mode = mode
