"""
macOS 프린터 연동
DNP DS620 프린터 지원
"""

import subprocess
import os


class MacPrinter:
    """macOS 프린터 연동 클래스"""

    def __init__(self, printer_name=None):
        """
        Args:
            printer_name: 프린터 이름 (None이면 기본 프린터)
        """
        self.printer_name = printer_name

    def list_printers(self):
        """
        시스템에 등록된 프린터 목록 반환

        Returns:
            list: 프린터 이름 목록
        """
        try:
            result = subprocess.run(
                ['lpstat', '-p'],
                capture_output=True,
                text=True,
                timeout=10
            )

            printers = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith('printer '):
                    # "printer PrinterName is idle" 형태
                    parts = line.split()
                    if len(parts) >= 2:
                        printers.append(parts[1])

            return printers
        except Exception as e:
            print(f"프린터 목록 조회 실패: {e}")
            return []

    def get_default_printer(self):
        """
        기본 프린터 이름 반환

        Returns:
            str or None: 기본 프린터 이름
        """
        try:
            result = subprocess.run(
                ['lpstat', '-d'],
                capture_output=True,
                text=True,
                timeout=10
            )

            # "system default destination: PrinterName" 형태
            output = result.stdout.strip()
            if 'destination:' in output:
                return output.split('destination:')[1].strip()
            return None
        except Exception as e:
            print(f"기본 프린터 조회 실패: {e}")
            return None

    def print_image_directly(self, image_path):
        """
        이미지를 Preview 앱으로 열기 (권장 방식)
        사용자가 직접 인쇄 설정을 확인하고 인쇄

        Args:
            image_path: 이미지 파일 경로

        Returns:
            tuple: (성공여부, 메시지)
        """
        if not os.path.exists(image_path):
            return False, f"파일을 찾을 수 없습니다: {image_path}"

        try:
            subprocess.run(
                ['open', '-a', 'Preview', image_path],
                check=True,
                timeout=10
            )
            return True, "Preview 앱에서 열렸습니다. Cmd+P로 인쇄하세요."
        except subprocess.CalledProcessError as e:
            return False, f"Preview 앱 열기 실패: {e}"
        except Exception as e:
            return False, f"오류 발생: {e}"

    def print_with_lpr(self, image_path, copies=1):
        """
        lpr 명령으로 직접 인쇄 (고급 사용자용)

        Args:
            image_path: 이미지 파일 경로
            copies: 인쇄 매수

        Returns:
            tuple: (성공여부, 메시지)
        """
        if not os.path.exists(image_path):
            return False, f"파일을 찾을 수 없습니다: {image_path}"

        try:
            cmd = ['lpr', '-#', str(copies)]

            if self.printer_name:
                cmd.extend(['-P', self.printer_name])

            cmd.append(image_path)

            subprocess.run(cmd, check=True, timeout=30)
            return True, f"인쇄 작업이 전송되었습니다 ({copies}매)"
        except subprocess.CalledProcessError as e:
            return False, f"인쇄 실패: {e}"
        except Exception as e:
            return False, f"오류 발생: {e}"

    def set_printer(self, printer_name):
        """프린터 이름 설정"""
        self.printer_name = printer_name

    def find_dnp_printer(self):
        """
        DNP 프린터 자동 검색

        Returns:
            str or None: DNP 프린터 이름
        """
        printers = self.list_printers()
        for p in printers:
            if 'DNP' in p.upper() or 'DS620' in p.upper():
                return p
        return None
