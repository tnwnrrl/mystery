#!/usr/bin/env python3
"""
한글 입력 TTS 프로그램 (오프라인 버전)
- 키보드로 한글 입력 시 TTS로 음성 재생
- 검정 배경에 흰색 자막 표시
- macOS say 명령어 사용 (인터넷 불필요)
"""

import tkinter as tk
from tkinter import font
import threading
import queue
import subprocess


class KoreanTTSApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("한글 TTS 자막")

        # 전체 화면 설정
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')

        # ESC 키로 종료
        self.root.bind('<Escape>', lambda e: self.root.quit())

        # TTS 큐
        self.tts_queue = queue.Queue()

        # sent_text: Enter 쳤을 때까지의 전체 텍스트 (Entry 내용 기준점)
        self.sent_text = ""

        # 자막 레이블 설정
        self.subtitle_font = font.Font(family='AppleGothic', size=72, weight='bold')
        self.subtitle_label = tk.Label(
            self.root,
            text="",
            font=self.subtitle_font,
            fg='white',
            bg='black',
            wraplength=self.root.winfo_screenwidth() - 100
        )
        self.subtitle_label.place(relx=0.5, rely=0.5, anchor='center')

        # 안내 텍스트
        self.info_label = tk.Label(
            self.root,
            text="한글을 입력하세요 (Enter: 재생, ESC: 종료)",
            font=('AppleGothic', 16),
            fg='gray',
            bg='black'
        )
        self.info_label.place(relx=0.5, rely=0.95, anchor='center')

        # 숨겨진 Entry 위젯 (한글 IME 입력용)
        self.entry_var = tk.StringVar()
        self.entry_var.trace_add('write', self.on_text_change)

        self.hidden_entry = tk.Entry(
            self.root,
            textvariable=self.entry_var,
            font=('AppleGothic', 1),
            bg='black',
            fg='black',
            insertbackground='black',
            highlightthickness=0,
            borderwidth=0
        )
        # Entry를 화면 밖에 배치 (보이지 않지만 포커스 가능)
        self.hidden_entry.place(x=-100, y=-100, width=1, height=1)

        # Enter 키 바인딩
        self.hidden_entry.bind('<KeyRelease-Return>', self.on_enter)

        # TTS 스레드 시작
        self.tts_thread = threading.Thread(target=self.tts_worker, daemon=True)
        self.tts_thread.start()

        # Entry에 포커스
        self.hidden_entry.focus_set()

        # 클릭 시 Entry에 포커스 유지
        self.root.bind('<Button-1>', lambda e: self.hidden_entry.focus_set())

    def on_text_change(self, *args):
        """텍스트 변경 시 자막 업데이트 - Entry는 건드리지 않고 표시만 조절"""
        full_text = self.entry_var.get()

        # sent_text 이후에 입력된 부분만 자막에 표시
        if full_text.startswith(self.sent_text):
            display_text = full_text[len(self.sent_text):]
        else:
            # 백스페이스로 sent_text 영역까지 삭제한 경우
            display_text = full_text
            self.sent_text = ""  # 리셋

        self.subtitle_label.config(text=display_text)

    def on_enter(self, event):
        """엔터 키 처리 - TTS 재생"""
        full_text = self.entry_var.get()

        # 새로 입력된 부분만 추출
        if full_text.startswith(self.sent_text):
            new_text = full_text[len(self.sent_text):]
        else:
            new_text = full_text

        new_text = new_text.strip()

        if new_text:
            self.tts_queue.put(new_text)
            # sent_text를 현재 전체 텍스트로 업데이트
            self.sent_text = full_text

        # Entry가 너무 길어지면 정리 (500자 이상)
        if len(full_text) > 500:
            self.root.after(100, self.cleanup_entry)

        return "break"

    def cleanup_entry(self):
        """Entry 정리 - IME 조합이 없을 때만"""
        # Entry를 비우고 sent_text도 리셋
        self.entry_var.set("")
        self.sent_text = ""

    def tts_worker(self):
        """TTS 처리 스레드"""
        while True:
            text = self.tts_queue.get()
            if text:
                try:
                    self.play_tts(text)
                except Exception as e:
                    print(f"TTS 오류: {e}")

    def play_tts(self, text):
        """TTS 음성 재생 - macOS say 명령어 사용 (오프라인)"""
        subprocess.run([
            'say',
            '-v', 'Yuna',  # 한국어 Yuna 음성
            text
        ], capture_output=True)

    def run(self):
        """앱 실행"""
        self.root.mainloop()


def main():
    app = KoreanTTSApp()
    app.run()


if __name__ == "__main__":
    main()
