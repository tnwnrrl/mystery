"""
macOS 프린터 연동
DNP DS620 프린터 지원
"""

import subprocess
import os


class MacPrinter:
    """macOS 프린터 연동 클래스"""

    # DNP DS620 프린터 옵션
    DNP_PRINTER_NAME = "Dai_Nippon_Printing_DP_DS620"
    DNP_PAGE_SIZE = "dnp6x8"  # 6x8인치
    DNP_CUTTER = "Normal"     # 자동 커팅

    def __init__(self, printer_name=None):
        """
        Args:
            printer_name: 프린터 이름 (None이면 DNP 프린터 자동 검색)
        """
        self.printer_name = printer_name or self.DNP_PRINTER_NAME

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

    def print_image_directly(self, image_path, copies=1):
        """
        lp 명령으로 DNP 프린터에 직접 인쇄 (자동 커팅 포함)

        Args:
            image_path: 이미지 파일 경로
            copies: 인쇄 매수

        Returns:
            tuple: (성공여부, 메시지)
        """
        if not os.path.exists(image_path):
            return False, f"파일을 찾을 수 없습니다: {image_path}"

        try:
            cmd = [
                'lp',
                '-d', self.printer_name,
                '-o', f'PageSize={self.DNP_PAGE_SIZE}',
                '-o', f'Cutter={self.DNP_CUTTER}',
                '-n', str(copies),
                image_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            # lp 출력에서 작업 ID 추출 (예: "request id is Printer-123")
            job_info = result.stdout.strip() if result.stdout else "인쇄 작업 전송됨"
            return True, f"인쇄 완료: {copies}매 ({self.DNP_PAGE_SIZE}, 자동커팅)"

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            return False, f"인쇄 실패: {error_msg}"
        except Exception as e:
            return False, f"오류 발생: {e}"

    def print_with_preview(self, image_path):
        """
        이미지를 Preview 앱으로 열기 (수동 인쇄)

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

    def print_individual_photos(self, file_paths, copies=1):
        """
        개별 사진들을 6x4 크기로 인쇄 (자동 커팅)
        프린터가 6x8 용지에 2장씩 모아서 인쇄하고 가운데서 커팅

        Args:
            file_paths: 이미지 파일 경로 목록
            copies: 각 사진 인쇄 매수

        Returns:
            tuple: (성공여부, 메시지)
        """
        if not file_paths:
            return False, "인쇄할 파일이 없습니다"

        success_count = 0
        errors = []

        for path in file_paths:
            if not os.path.exists(path):
                errors.append(f"파일 없음: {path}")
                continue

            try:
                cmd = [
                    'lp',
                    '-d', self.printer_name,
                    '-o', 'PageSize=dnp6x4',  # 6x4인치 개별 사진
                    '-o', f'Cutter={self.DNP_CUTTER}',
                    '-n', str(copies),
                    path
                ]

                subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30
                )
                success_count += 1

            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() if e.stderr else str(e)
                errors.append(f"{os.path.basename(path)}: {error_msg}")
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")

        if success_count == len(file_paths):
            return True, f"인쇄 완료: {success_count}장 (6x4, 자동커팅)"
        elif success_count > 0:
            return True, f"부분 완료: {success_count}/{len(file_paths)}장\n오류: {'; '.join(errors)}"
        else:
            return False, f"인쇄 실패: {'; '.join(errors)}"
