#!/usr/bin/env python3
"""
Canon 100D 사진 자동 처리 GUI 프로그램

기능:
- 모니터링 시작/종료 버튼
- AI 변환 / 오버레이 합성 하이브리드 모드
- 실시간 로그 출력
- 처리 통계 표시
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
import queue
import sys
import os
import json
import subprocess
from datetime import datetime
# PIL 제외 (macOS 버전 호환성 문제)

# 카메라 모듈 (gphoto2 없으면 None)
try:
    from utils.camera import CameraConnection
    CAMERA_AVAILABLE = True
except ImportError:
    CameraConnection = None
    CAMERA_AVAILABLE = False
    print("⚠️ gphoto2 미설치 - 카메라 기능 비활성화 (수동 모드 사용)")

from utils.ai_transformer import HybridProcessor, check_internet


def kill_camera_processes():
    """카메라를 점유하고 있는 프로세스 강제 종료 (start.command와 동일)"""
    try:
        # start.command와 동일한 강력한 프로세스 정리
        subprocess.run(['pkill', '-9', '-f', 'ptpcamerad'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-9', '-f', 'mscamerad'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-9', '-f', 'icdd'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-9', '-f', 'cameracaptured'], stderr=subprocess.DEVNULL)
        subprocess.run(['killall', '-9', 'Image Capture'], stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


class PhotoProcessorGUI:
    """GUI 메인 클래스"""

    def __init__(self, root):
        self.root = root
        self.root.title("Canon 100D 사진 자동 처리")
        self.root.geometry("900x800")

        # 상태 변수
        self.is_monitoring = False
        self.monitor_thread = None
        self.log_queue = queue.Queue()

        # 통계
        self.stats = {
            'downloaded': 0,
            'ai_processed': 0,
            'overlay_processed': 0,
            'errors': 0
        }

        # 상태 업데이트 타이머
        self.status_update_job = None

        # 설정 로드
        self.load_config()

        # UI 생성
        self.create_widgets()

        # 로그 큐 체크
        self.check_log_queue()

        # 상태 업데이트
        self.update_ai_status()

    def load_config(self):
        """설정 파일 로드"""
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.original_folder = self.config['paths']['original_folder']
        self.overlay_image = self.config['paths']['overlay_image']
        self.output_folder = self.config['paths']['output_folder']
        self.check_interval = self.config['camera']['check_interval_seconds']
        self.processed_files_db = self.config['monitoring']['processed_files_db']

        # AI 설정
        self.ai_config = self.config.get('ai', {})
        self.processing_mode = self.config.get('processing', {}).get('mode', 'hybrid')

    def save_config(self):
        """설정 파일 저장"""
        self.config['paths']['original_folder'] = self.original_folder
        self.config['paths']['overlay_image'] = self.overlay_image
        self.config['paths']['output_folder'] = self.output_folder
        self.config['ai'] = self.ai_config
        self.config['processing']['mode'] = self.processing_mode

        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def create_widgets(self):
        """UI 위젯 생성"""
        # 상단 프레임 - 제목
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)

        title_label = ttk.Label(
            title_frame,
            text="Canon 100D 사진 자동 처리",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack()

        # 노트북 (탭)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 탭 1: 메인
        main_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(main_tab, text="메인")
        self.create_main_tab(main_tab)

        # 탭 2: AI 설정
        ai_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(ai_tab, text="AI 설정")
        self.create_ai_tab(ai_tab)

        # 탭 3: 폴더 설정
        folder_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(folder_tab, text="폴더 설정")
        self.create_folder_tab(folder_tab)

    def create_main_tab(self, parent):
        """메인 탭 생성"""
        # 처리 모드 선택
        mode_frame = ttk.LabelFrame(parent, text="처리 모드", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)

        self.mode_var = tk.StringVar(value=self.processing_mode)

        modes = [
            ("하이브리드 (AI 우선, 오프라인 시 오버레이)", "hybrid"),
            ("AI 전용 (인터넷 필수)", "ai"),
            ("오버레이 전용 (오프라인 가능)", "overlay")
        ]

        for text, mode in modes:
            rb = ttk.Radiobutton(mode_frame, text=text, variable=self.mode_var,
                                value=mode, command=self.on_mode_change)
            rb.pack(anchor=tk.W, pady=2)

        # AI 상태 표시
        self.ai_status_frame = ttk.LabelFrame(parent, text="AI 상태", padding="10")
        self.ai_status_frame.pack(fill=tk.X, pady=5)

        self.ai_status_label = ttk.Label(self.ai_status_frame, text="확인 중...")
        self.ai_status_label.pack(anchor=tk.W)

        self.internet_status_label = ttk.Label(self.ai_status_frame, text="")
        self.internet_status_label.pack(anchor=tk.W)

        ttk.Button(self.ai_status_frame, text="상태 새로고침",
                  command=self.update_ai_status).pack(anchor=tk.W, pady=5)

        # 통계 프레임
        stats_frame = ttk.LabelFrame(parent, text="처리 통계", padding="10")
        stats_frame.pack(fill=tk.X, pady=5)

        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack()

        ttk.Label(stats_grid, text="다운로드:").grid(row=0, column=0, padx=5)
        self.downloaded_label = ttk.Label(stats_grid, text="0", font=("Helvetica", 12, "bold"))
        self.downloaded_label.grid(row=0, column=1, padx=5)

        ttk.Label(stats_grid, text="AI 변환:").grid(row=0, column=2, padx=5)
        self.ai_processed_label = ttk.Label(stats_grid, text="0", font=("Helvetica", 12, "bold"), foreground="blue")
        self.ai_processed_label.grid(row=0, column=3, padx=5)

        ttk.Label(stats_grid, text="오버레이:").grid(row=0, column=4, padx=5)
        self.overlay_processed_label = ttk.Label(stats_grid, text="0", font=("Helvetica", 12, "bold"), foreground="green")
        self.overlay_processed_label.grid(row=0, column=5, padx=5)

        ttk.Label(stats_grid, text="오류:").grid(row=0, column=6, padx=5)
        self.errors_label = ttk.Label(stats_grid, text="0", font=("Helvetica", 12, "bold"), foreground="red")
        self.errors_label.grid(row=0, column=7, padx=5)

        # 컨트롤 프레임
        control_frame = ttk.Frame(parent, padding="10")
        control_frame.pack(fill=tk.X)

        # 수동 처리 버튼 (항상 사용 가능)
        self.manual_button = ttk.Button(
            control_frame,
            text="📁 수동 처리",
            command=self.manual_process
        )
        self.manual_button.pack(side=tk.LEFT, padx=5)

        self.start_button = ttk.Button(
            control_frame,
            text="▶ 모니터링 시작",
            command=self.start_monitoring,
            state=tk.NORMAL if CAMERA_AVAILABLE else tk.DISABLED
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            control_frame,
            text="⏹ 모니터링 종료",
            command=self.stop_monitoring,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.reconnect_button = ttk.Button(
            control_frame,
            text="🔄 카메라 재연결",
            command=self.reconnect_camera,
            state=tk.NORMAL if CAMERA_AVAILABLE else tk.DISABLED
        )
        self.reconnect_button.pack(side=tk.LEFT, padx=5)

        # 상태
        self.status_label = ttk.Label(
            control_frame,
            text="⚪ 대기 중",
            font=("Helvetica", 12)
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # 미리보기 + 로그 컨테이너
        preview_log_frame = ttk.Frame(parent)
        preview_log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 미리보기 프레임 (왼쪽)
        preview_frame = ttk.LabelFrame(preview_log_frame, text="최근 처리 이미지", padding="10")
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))

        self.preview_label = ttk.Label(preview_frame, text="처리된 이미지 없음", anchor=tk.CENTER)
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        self.preview_info_label = ttk.Label(preview_frame, text="", font=("Helvetica", 9))
        self.preview_info_label.pack(pady=5)

        # 로그 프레임 (오른쪽)
        log_frame = ttk.LabelFrame(preview_log_frame, text="실시간 로그", padding="10")
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            wrap=tk.WORD,
            font=("Courier", 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 하단 버튼
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill=tk.X, pady=5)

        ttk.Button(bottom_frame, text="로그 지우기",
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)

        ttk.Button(bottom_frame, text="종료",
                  command=self.quit_app).pack(side=tk.RIGHT, padx=5)

    def create_ai_tab(self, parent):
        """AI 설정 탭 생성"""
        # API 키
        api_frame = ttk.LabelFrame(parent, text="Gemini API 설정", padding="10")
        api_frame.pack(fill=tk.X, pady=5)

        ttk.Label(api_frame, text="API 키:").pack(anchor=tk.W)
        self.api_key_var = tk.StringVar(value=self.ai_config.get('api_key', ''))
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=60, show="*")
        api_entry.pack(fill=tk.X, pady=2)

        key_btn_frame = ttk.Frame(api_frame)
        key_btn_frame.pack(fill=tk.X, pady=2)

        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(key_btn_frame, text="키 표시",
                       variable=self.show_key_var,
                       command=lambda: api_entry.config(show="" if self.show_key_var.get() else "*")
                       ).pack(side=tk.LEFT)

        ttk.Label(api_frame, text="모델:").pack(anchor=tk.W, pady=(10, 0))
        self.model_var = tk.StringVar(value=self.ai_config.get('model', 'gemini-2.5-flash-preview-05-20'))
        model_combo = ttk.Combobox(api_frame, textvariable=self.model_var, width=40,
                                   values=['gemini-2.5-flash-preview-05-20',
                                          'gemini-2.0-flash-exp'])
        model_combo.pack(fill=tk.X, pady=2)

        # 프롬프트
        prompt_frame = ttk.LabelFrame(parent, text="AI 프롬프트", padding="10")
        prompt_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(prompt_frame, text="이미지 변환 지시 (한국어 지원):").pack(anchor=tk.W)

        self.prompt_text = scrolledtext.ScrolledText(
            prompt_frame,
            height=8,
            wrap=tk.WORD,
            font=("Courier", 10)
        )
        self.prompt_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.prompt_text.insert(tk.END, self.ai_config.get('prompt', ''))

        # 저장 버튼
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="💾 AI 설정 저장",
                  command=self.save_ai_settings).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="🔄 기본값 복원",
                  command=self.reset_ai_settings).pack(side=tk.LEFT, padx=5)

        # 비용 안내
        cost_frame = ttk.LabelFrame(parent, text="비용 안내", padding="10")
        cost_frame.pack(fill=tk.X, pady=5)

        cost_text = """• 이미지당 약 $0.039 (약 50원)
• 무료 티어: Google AI Studio에서 약 1,500장/일
• 오프라인 시 자동으로 오버레이 폴백 (하이브리드 모드)"""

        ttk.Label(cost_frame, text=cost_text, justify=tk.LEFT).pack(anchor=tk.W)

    def create_folder_tab(self, parent):
        """폴더 설정 탭 생성"""
        # 다운로드 폴더
        download_frame = ttk.LabelFrame(parent, text="다운로드 폴더", padding="10")
        download_frame.pack(fill=tk.X, pady=5)

        self.download_folder_var = tk.StringVar(value=self.original_folder)
        ttk.Entry(download_frame, textvariable=self.download_folder_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(download_frame, text="찾아보기",
                  command=lambda: self.browse_folder(self.download_folder_var, 'original_folder')).pack(side=tk.RIGHT)

        # 출력 폴더
        output_frame = ttk.LabelFrame(parent, text="출력 폴더", padding="10")
        output_frame.pack(fill=tk.X, pady=5)

        self.output_folder_var = tk.StringVar(value=self.output_folder)
        ttk.Entry(output_frame, textvariable=self.output_folder_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="찾아보기",
                  command=lambda: self.browse_folder(self.output_folder_var, 'output_folder')).pack(side=tk.RIGHT)

        # 오버레이 이미지 (폴백용)
        overlay_frame = ttk.LabelFrame(parent, text="오버레이 이미지 (폴백용)", padding="10")
        overlay_frame.pack(fill=tk.X, pady=5)

        self.overlay_image_var = tk.StringVar(value=self.overlay_image)
        ttk.Entry(overlay_frame, textvariable=self.overlay_image_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(overlay_frame, text="찾아보기",
                  command=self.browse_overlay_file).pack(side=tk.RIGHT)

        # 설명
        desc_frame = ttk.Frame(parent, padding="10")
        desc_frame.pack(fill=tk.X, pady=10)

        desc_text = """📁 다운로드 폴더: 카메라에서 가져온 원본 사진 저장
📁 출력 폴더: AI 변환 또는 오버레이 합성된 사진 저장
🖼️ 오버레이 이미지: AI 실패 시 폴백으로 사용할 PNG 이미지"""

        ttk.Label(desc_frame, text=desc_text, justify=tk.LEFT).pack(anchor=tk.W)

    def on_mode_change(self):
        """처리 모드 변경"""
        self.processing_mode = self.mode_var.get()
        self.save_config()
        self.log(f"✅ 처리 모드 변경: {self.processing_mode}")
        self.update_ai_status()

    def update_ai_status(self):
        """AI 상태 업데이트"""
        # 인터넷 연결 확인
        internet_ok = check_internet()
        internet_text = "🌐 인터넷: 연결됨" if internet_ok else "🌐 인터넷: 연결 안됨"
        self.internet_status_label.config(text=internet_text,
                                          foreground="green" if internet_ok else "red")

        # API 키 확인
        api_key = self.ai_config.get('api_key', '')
        if not api_key:
            self.ai_status_label.config(text="⚠️ API 키 미설정 (AI 탭에서 설정)", foreground="orange")
        elif not internet_ok:
            self.ai_status_label.config(text="⚠️ 오프라인 - 오버레이 폴백 사용", foreground="orange")
        else:
            self.ai_status_label.config(text="✅ AI 변환 준비됨", foreground="green")

    def update_preview(self, image_path: str, method: str):
        """처리된 이미지 미리보기 업데이트 (텍스트 기반)"""
        try:
            # 파일명과 방식 표시
            filename = os.path.basename(image_path)
            method_text = "🤖 AI 변환" if method == 'ai' else "🖼️ 오버레이"
            
            # 파일 크기
            file_size = os.path.getsize(image_path)
            size_text = f"{file_size // 1024} KB"
            
            # 라벨 업데이트
            self.preview_label.config(text=f"✅ {filename}\n({size_text})")
            self.preview_info_label.config(text=method_text)

        except Exception as e:
            self.log(f"⚠️ 미리보기 로드 실패: {e}")

    def schedule_status_update(self):
        """10초마다 AI 상태 자동 업데이트"""
        if self.is_monitoring:
            self.update_ai_status()
            self.status_update_job = self.root.after(10000, self.schedule_status_update)

    def cancel_status_update(self):
        """상태 업데이트 타이머 취소"""
        if self.status_update_job:
            self.root.after_cancel(self.status_update_job)
            self.status_update_job = None

    def save_ai_settings(self):
        """AI 설정 저장"""
        self.ai_config['api_key'] = self.api_key_var.get().strip()
        self.ai_config['model'] = self.model_var.get().strip()
        self.ai_config['prompt'] = self.prompt_text.get("1.0", tk.END).strip()

        self.save_config()
        self.log("✅ AI 설정 저장 완료")
        self.update_ai_status()

    def reset_ai_settings(self):
        """AI 설정 기본값 복원"""
        default_prompt = """이 사진을 심령사진처럼 편집해줘:
1. 인형의 눈을 붉게 빛나는 악마의 눈으로 바꿔줘
2. 사람들 주변 어두운 배경에 희미하게 일렁이는 유령 형체를 추가해줘
3. 원본 사람들의 얼굴, 옷, 포즈는 절대 바꾸지 마
4. 전체적으로 오싹한 분위기로"""

        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert(tk.END, default_prompt)
        self.model_var.set('gemini-2.5-flash-preview-05-20')
        self.log("🔄 AI 설정 기본값 복원")

    def log(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}\n")

    def check_log_queue(self):
        """로그 큐에서 메시지 가져와 표시"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass

        # 100ms마다 체크
        self.root.after(100, self.check_log_queue)

    def update_stats(self):
        """통계 업데이트"""
        self.downloaded_label.config(text=str(self.stats['downloaded']))
        self.ai_processed_label.config(text=str(self.stats['ai_processed']))
        self.overlay_processed_label.config(text=str(self.stats['overlay_processed']))
        self.errors_label.config(text=str(self.stats['errors']))

    def clear_log(self):
        """로그 지우기"""
        self.log_text.delete(1.0, tk.END)

    def start_monitoring(self):
        """모니터링 시작"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="🟢 모니터링 중")

        self.log("=" * 50)
        self.log(f"모니터링 시작 (모드: {self.processing_mode})")
        self.log("=" * 50)

        # 백그라운드 스레드 시작
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()

        # 상태 자동 업데이트 시작
        self.schedule_status_update()

    def stop_monitoring(self):
        """모니터링 종료"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="⚪ 대기 중")

        # 상태 업데이트 타이머 취소
        self.cancel_status_update()

        self.log("=" * 50)
        self.log("모니터링 종료")
        self.log("=" * 50)

    def monitoring_loop(self):
        """모니터링 루프 (백그라운드)"""
        import time

        # 처리된 파일 목록 로드
        processed_files = self.load_processed_files()

        # 최신 설정 로드
        self.load_config()

        # 하이브리드 프로세서 초기화
        processor = HybridProcessor(self.config)
        processor.set_mode(self.processing_mode)

        status = processor.get_status()
        self.log(f"  AI 상태: {status['ai_reason']}")
        self.log(f"  오버레이 상태: {'준비됨' if status['overlay_available'] else '미설정'}")

        # 카메라 연결 (한 번만)
        camera = CameraConnection()
        if not camera.connect():
            self.log("❌ 카메라 연결 실패")
            self.root.after(0, self.stop_monitoring)
            return

        self.log(f"✅ 카메라 연결 유지: {camera.camera_name}")

        while self.is_monitoring:
            new_files = []

            try:
                self.log(f"🔍 카메라 스캔 중... ({self.check_interval}초 간격)")
                
                # 연결 상태 확인
                if not camera.is_connected:
                    self.log("⚠️ 카메라 연결 끊김, 재연결 시도...")
                    if not camera.connect():
                        self.log("❌ 재연결 실패")
                        time.sleep(self.check_interval)
                        continue

                # 새 파일 확인 및 다운로드
                all_files = camera.get_all_files()
                self.log(f"  📁 카메라 파일 수: {len(all_files)}개")
                
                # 파일이 0개면 연결 문제일 수 있음 - 재연결 시도
                if len(all_files) == 0 and camera.is_connected:
                    self.log("⚠️ 파일 0개 - 연결 확인 중...")
                    camera.is_connected = False
                    if camera.connect():
                        self.log("✅ 재연결 성공")
                        all_files = camera.get_all_files()
                        self.log(f"  📁 재스캔 파일 수: {len(all_files)}개")
                    else:
                        self.log("❌ 재연결 실패")
                        time.sleep(self.check_interval)
                        continue

                for file_info in all_files:
                    if file_info['full_path'] in processed_files:
                        continue

                    if camera.download_file(file_info, self.original_folder):
                        new_files.append(file_info['name'])
                        processed_files.add(file_info['full_path'])
                        self.stats['downloaded'] += 1
                        self.log(f"  ✅ {file_info['name']} 다운로드 완료")

                # 이미지 처리 (하이브리드)
                if new_files:
                    self.log(f"✅ 새 파일 {len(new_files)}개 발견!")

                    for filename in new_files:
                        input_path = os.path.join(self.original_folder, filename)
                        output_path = os.path.join(self.output_folder, filename)

                        success, method, msg = processor.process_image(input_path, output_path)

                        if success:
                            if method == 'ai':
                                self.stats['ai_processed'] += 1
                                self.log(f"  🤖 {filename} AI 변환 완료")
                            else:
                                self.stats['overlay_processed'] += 1
                                self.log(f"  🖼️ {filename} 오버레이 합성 ({msg})")
                            # 미리보기 업데이트 (메인 스레드에서)
                            self.root.after(0, lambda p=output_path, m=method: self.update_preview(p, m))
                        else:
                            self.stats['errors'] += 1
                            self.log(f"  ❌ {filename} 처리 실패: {msg}")

                    self.root.after(0, self.update_stats)
                    self.save_processed_files(processed_files)

            except Exception as e:
                self.log(f"❌ 오류: {e}")
                self.stats['errors'] += 1
                self.root.after(0, self.update_stats)
                # 오류 시 연결 상태 리셋
                camera.is_connected = False

            # 대기
            time.sleep(self.check_interval)

        # 모니터링 종료 시 연결 해제
        camera.disconnect()
        self.log("📴 카메라 연결 해제")

    def load_processed_files(self):
        """처리된 파일 목록 로드"""
        if os.path.exists(self.processed_files_db):
            with open(self.processed_files_db, 'r') as f:
                return set(json.load(f))
        return set()

    def save_processed_files(self, processed_files):
        """처리된 파일 목록 저장"""
        with open(self.processed_files_db, 'w') as f:
            json.dump(list(processed_files), f, indent=2)

    def browse_folder(self, var, config_key):
        """폴더 선택 다이얼로그"""
        current_path = var.get()
        folder_path = filedialog.askdirectory(
            title="폴더 선택",
            initialdir=current_path if os.path.exists(current_path) else "."
        )

        if folder_path:
            var.set(folder_path)
            # 설정 업데이트
            if config_key == 'original_folder':
                self.original_folder = folder_path
            elif config_key == 'output_folder':
                self.output_folder = folder_path

            self.save_config()
            self.log(f"✅ {config_key} 경로 변경: {folder_path}")

    def browse_overlay_file(self):
        """오버레이 파일 선택 다이얼로그"""
        current_path = self.overlay_image_var.get()
        file_path = filedialog.askopenfilename(
            title="PNG 파일 선택",
            initialdir=os.path.dirname(current_path) if os.path.exists(current_path) else ".",
            filetypes=[("PNG 파일", "*.png"), ("모든 파일", "*.*")]
        )

        if file_path:
            self.overlay_image_var.set(file_path)
            self.overlay_image = file_path
            self.save_config()
            self.log(f"✅ 오버레이 이미지 변경: {file_path}")

    def manual_process(self):
        """수동으로 이미지 선택하여 처리"""
        file_paths = filedialog.askopenfilenames(
            title="처리할 이미지 선택",
            filetypes=[("이미지 파일", "*.jpg *.jpeg *.png"), ("모든 파일", "*.*")]
        )

        if not file_paths:
            return

        self.log(f"📁 수동 처리 시작: {len(file_paths)}개 파일")

        # 최신 설정 로드
        self.load_config()

        # 하이브리드 프로세서 초기화
        processor = HybridProcessor(self.config)
        processor.set_mode(self.processing_mode)

        for file_path in file_paths:
            filename = os.path.basename(file_path)
            output_path = os.path.join(self.output_folder, filename)

            self.log(f"  처리 중: {filename}")

            success, method, msg = processor.process_image(file_path, output_path)

            if success:
                if method == 'ai':
                    self.stats['ai_processed'] += 1
                    self.log(f"  🤖 {filename} AI 변환 완료")
                else:
                    self.stats['overlay_processed'] += 1
                    self.log(f"  🖼️ {filename} 오버레이 합성")
                # 미리보기 업데이트
                self.update_preview(output_path, method)
            else:
                self.stats['errors'] += 1
                self.log(f"  ❌ {filename} 실패: {msg}")

        self.update_stats()
        self.log(f"✅ 수동 처리 완료")

    def reconnect_camera(self):
        """카메라 재연결 시도 (start.command와 동일한 3회 재시도)"""
        import time

        self.log("🔄 카메라 재연결 시도 중...")
        self.log("  🔧 카메라 프로세스 정리...")

        MAX_ATTEMPTS = 3
        connected = False

        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.log(f"  시도 {attempt}/{MAX_ATTEMPTS}...")

            # 1. 카메라 프로세스 강제 종료
            kill_camera_processes()
            time.sleep(1)

            # 2. 카메라 연결 시도
            try:
                camera = CameraConnection()
                if camera.connect():
                    self.log(f"✅ 카메라 재연결 성공: {camera.camera_name}")
                    camera.disconnect()
                    connected = True
                    break
            except Exception as e:
                self.log(f"   ❌ 실패: {e}")

            # 재시도 전 프로세스 재정리 및 대기
            if attempt < MAX_ATTEMPTS:
                kill_camera_processes()
                time.sleep(2)

        if not connected:
            self.log("❌ 카메라 재연결 실패 (3회 시도 모두 실패)")
            self.log("💡 해결 방법: USB 케이블을 뽑았다가 다시 연결 후 재시도")

    def quit_app(self):
        """프로그램 종료 (start.command와 동일한 강력한 프로세스 정리)"""
        if self.is_monitoring:
            self.stop_monitoring()

        # 카메라 점유 프로세스 강제 종료 (start.command와 동일)
        self.log("🧹 카메라 프로세스 강제 정리 중...")
        self.log("  🔧 ptpcamerad, mscamerad, icdd, cameracaptured, Image Capture 종료...")
        kill_camera_processes()
        self.log("  ✅ 모든 카메라 프로세스 정리 완료")
        self.log("✅ 프로그램 종료")

        self.root.quit()


def main():
    """메인 실행 함수"""
    # 설정 파일 확인
    if not os.path.exists("config.json"):
        print("❌ config.json 파일을 찾을 수 없습니다.")
        sys.exit(1)

    # 카메라 점유 프로세스 자동 종료
    print("🔄 카메라 점유 프로세스 확인 중...")
    kill_camera_processes()
    print("✅ 카메라 점유 프로세스 종료 완료")

    # GUI 실행
    root = tk.Tk()
    app = PhotoProcessorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()


if __name__ == "__main__":
    main()
