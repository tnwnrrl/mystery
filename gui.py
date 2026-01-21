#!/usr/bin/env python3
"""
6컷 레이아웃 앱
DNP DS620 6x8" 용지에 2x3 그리드로 사진 6장 배치
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import json
from datetime import datetime

from utils.layout_engine import LayoutEngine
from utils.printer import MacPrinter


class LayoutApp:
    """6컷 레이아웃 메인 앱"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("6컷 레이아웃 - DNP DS620")
        self.root.geometry("800x650")
        self.root.resizable(False, False)

        # 엔진 및 프린터
        self.engine = LayoutEngine(fit_mode='fill')
        self.printer = MacPrinter()

        # 설정 로드
        self.config = self._load_config()
        self.output_dir = self.config.get('output_dir', 'output')
        os.makedirs(self.output_dir, exist_ok=True)

        # 슬롯 버튼 참조
        self.slot_buttons = []
        self.slot_labels = []
        self.slot_paths = [None] * 6

        # 미리보기 이미지 참조 (GC 방지)
        self.preview_photo = None

        # fit 모드 변수
        self.fit_mode_var = tk.StringVar(value='fill')

        self._setup_ui()
        self._update_preview()

    def _load_config(self):
        """설정 파일 로드"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _setup_ui(self):
        """UI 구성"""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 좌측: 슬롯 선택 영역
        left_frame = ttk.LabelFrame(main_frame, text="이미지 선택", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self._create_slot_buttons(left_frame)

        # 전체 비우기 버튼
        ttk.Button(
            left_frame,
            text="전체 비우기",
            command=self._clear_all
        ).pack(pady=(20, 0), fill=tk.X)

        # 폴더에서 6장 로드 버튼
        ttk.Button(
            left_frame,
            text="폴더에서 6장 로드",
            command=self._load_from_folder
        ).pack(pady=(5, 0), fill=tk.X)

        # 우측: 미리보기 및 액션
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 미리보기 캔버스
        preview_label = ttk.Label(right_frame, text="미리보기 (6x8\")")
        preview_label.pack()

        # 450x600 미리보기 (1800x2400의 1/4)
        self.preview_canvas = tk.Canvas(
            right_frame,
            width=450,
            height=600,
            bg='white',
            relief='sunken',
            bd=2
        )
        self.preview_canvas.pack(pady=10)

        # 모드 선택
        mode_frame = ttk.Frame(right_frame)
        mode_frame.pack(pady=5)

        ttk.Label(mode_frame, text="맞춤 모드:").pack(side=tk.LEFT, padx=(0, 10))

        ttk.Radiobutton(
            mode_frame,
            text="채우기 (크롭)",
            variable=self.fit_mode_var,
            value='fill',
            command=self._on_mode_change
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            mode_frame,
            text="맞추기 (여백)",
            variable=self.fit_mode_var,
            value='fit',
            command=self._on_mode_change
        ).pack(side=tk.LEFT, padx=5)

        # 액션 버튼
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(pady=20)

        ttk.Button(
            action_frame,
            text="저장",
            command=self._save_layout,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            action_frame,
            text="인쇄",
            command=self._print_layout,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        # 상태 표시
        self.status_var = tk.StringVar(value="이미지를 선택하세요")
        status_label = ttk.Label(
            right_frame,
            textvariable=self.status_var,
            foreground='gray'
        )
        status_label.pack(pady=10)

    def _create_slot_buttons(self, parent):
        """6개 슬롯 버튼 생성"""
        grid_frame = ttk.Frame(parent)
        grid_frame.pack()

        for i in range(6):
            row = i // 2
            col = i % 2

            slot_frame = ttk.Frame(grid_frame)
            slot_frame.grid(row=row, column=col, padx=5, pady=5)

            # 썸네일 버튼 (120x100)
            btn = tk.Button(
                slot_frame,
                text=f"{i+1}",
                width=14,
                height=6,
                bg='#f0f0f0',
                command=lambda idx=i: self._select_image(idx)
            )
            btn.pack()

            # 파일명 라벨
            label = ttk.Label(slot_frame, text="(비어있음)", width=16)
            label.pack()

            self.slot_buttons.append(btn)
            self.slot_labels.append(label)

    def _select_image(self, index):
        """슬롯에 이미지 선택"""
        filetypes = [
            ("이미지 파일", "*.jpg *.jpeg *.png *.bmp"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("모든 파일", "*.*")
        ]

        path = filedialog.askopenfilename(
            title=f"슬롯 {index+1} 이미지 선택",
            filetypes=filetypes
        )

        if path:
            self._load_image_to_slot(index, path)

    def _load_image_to_slot(self, index, path):
        """슬롯에 이미지 로드"""
        if self.engine.load_image(index, path):
            self.slot_paths[index] = path
            filename = os.path.basename(path)

            # 라벨 업데이트 (파일명 15자 제한)
            display_name = filename[:15] + "..." if len(filename) > 15 else filename
            self.slot_labels[index].config(text=display_name)

            # 버튼 색상 변경
            self.slot_buttons[index].config(bg='#90EE90')  # 연녹색

            self._update_preview()
            self._update_status()
        else:
            messagebox.showerror("오류", f"이미지를 로드할 수 없습니다:\n{path}")

    def _clear_slot(self, index):
        """슬롯 비우기"""
        self.engine.clear_image(index)
        self.slot_paths[index] = None
        self.slot_labels[index].config(text="(비어있음)")
        self.slot_buttons[index].config(bg='#f0f0f0')
        self._update_preview()
        self._update_status()

    def _clear_all(self):
        """모든 슬롯 비우기"""
        for i in range(6):
            self._clear_slot(i)

    def _load_from_folder(self):
        """폴더에서 처음 6개 이미지 로드"""
        folder = filedialog.askdirectory(title="이미지 폴더 선택")
        if not folder:
            return

        # 이미지 파일 검색
        extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        images = sorted([
            f for f in os.listdir(folder)
            if f.lower().endswith(extensions)
        ])

        if not images:
            messagebox.showinfo("알림", "폴더에 이미지가 없습니다.")
            return

        # 최대 6개 로드
        self._clear_all()
        for i, img_name in enumerate(images[:6]):
            path = os.path.join(folder, img_name)
            self._load_image_to_slot(i, path)

        count = min(len(images), 6)
        self.status_var.set(f"{count}개 이미지 로드됨")

    def _on_mode_change(self):
        """fill/fit 모드 변경"""
        self.engine.set_fit_mode(self.fit_mode_var.get())
        self._update_preview()

    def _update_preview(self):
        """미리보기 업데이트"""
        preview = self.engine.generate_preview(scale=0.25)
        self.preview_photo = ImageTk.PhotoImage(preview)

        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            225, 300,  # 중앙
            image=self.preview_photo,
            anchor=tk.CENTER
        )

        # 그리드 선 그리기
        self._draw_grid_lines()

    def _draw_grid_lines(self):
        """미리보기에 그리드 선 표시"""
        # 세로선 (중앙)
        self.preview_canvas.create_line(225, 0, 225, 600, fill='#cccccc', dash=(2, 2))

        # 가로선 (1/3, 2/3)
        self.preview_canvas.create_line(0, 200, 450, 200, fill='#cccccc', dash=(2, 2))
        self.preview_canvas.create_line(0, 400, 450, 400, fill='#cccccc', dash=(2, 2))

    def _update_status(self):
        """상태 표시 업데이트"""
        count = self.engine.get_slot_count()
        if count == 0:
            self.status_var.set("이미지를 선택하세요")
        elif count < 6:
            self.status_var.set(f"{count}/6 이미지 선택됨")
        else:
            self.status_var.set("6개 이미지 준비됨 - 저장 또는 인쇄 가능")

    def _save_layout(self):
        """레이아웃 저장"""
        if self.engine.get_slot_count() == 0:
            messagebox.showwarning("경고", "최소 1개 이상의 이미지를 선택하세요.")
            return

        # 기본 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"layout_{timestamp}.jpg"

        path = filedialog.asksaveasfilename(
            title="레이아웃 저장",
            defaultextension=".jpg",
            initialdir=self.output_dir,
            initialfile=default_name,
            filetypes=[("JPEG", "*.jpg"), ("모든 파일", "*.*")]
        )

        if path:
            if self.engine.save_layout(path):
                messagebox.showinfo("완료", f"저장 완료:\n{path}")
                self.status_var.set(f"저장됨: {os.path.basename(path)}")
            else:
                messagebox.showerror("오류", "저장에 실패했습니다.")

    def _print_layout(self):
        """레이아웃 인쇄"""
        if self.engine.get_slot_count() == 0:
            messagebox.showwarning("경고", "최소 1개 이상의 이미지를 선택하세요.")
            return

        # 임시 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = os.path.join(self.output_dir, f"print_{timestamp}.jpg")

        if not self.engine.save_layout(temp_path):
            messagebox.showerror("오류", "인쇄용 파일 생성에 실패했습니다.")
            return

        # Preview 앱으로 열기
        success, message = self.printer.print_image_directly(temp_path)

        if success:
            self.status_var.set(message)
            messagebox.showinfo("인쇄", message)
        else:
            messagebox.showerror("오류", message)

    def run(self):
        """앱 실행"""
        self.root.mainloop()


def main():
    app = LayoutApp()
    app.run()


if __name__ == "__main__":
    main()
