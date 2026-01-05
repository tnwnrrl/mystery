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
import re


class KoreanTTSApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("한글 TTS 자막")

        # 전체 화면 설정
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')

        # ESC 키로 종료
        self.root.bind('<Escape>', lambda e: self.root.quit())

        # 대본 딕셔너리 (F1~F10)
        self.scripts = {
            'F1': "누군데 마음대로 남의 가게에 들어오나! 문도 잠궈 놨는데 어떻게 들어온거야? 여긴 어떻게 찾아왔어?",
            'F2': "여기까지 흘러 왔다는건 그만한 이유가 있겠지. 거기 옆에 매고 있는 인형 그거 한번 줘봐.",
            'F3': "이거 확인을 해 봐야겠는데 일단 이놈 먼저 처리해야 하는데 나 좀 도와 주게나 그럼 나도 자네들을 도와주지.",
            'F4': "먼저 여기 책상에 있는 표를 보고 주파수를 먼저 맞춰봐. 주파수를 잘 맞추면 TV 채널을 맞출 수 있는 방법을 들을 수 있을게야.",
            'F5': "덕분에 빨리 봉인할 수 있었네. 나는 이렇게 인형이나 물건에 깃들어 있는 악령이나 사념을 다루는 일을 하고 있네. 자네들이 가져온 인형을 나에게 줘 보겠나?",
            'F6': "이 방법으로는 안되겠구만 날 따라오게.",
            'F7': "이 곳은 물건의 사념을 찍을 수 있는 곳이라네. 자네들 앞에 있는 제단에 인형을 올려두고, 마치 가족사진을 찍듯이 다정하게 포즈를 취해주게. 가족같은 느낌이 아니면 사념이 찍히지 않으니 최대한 다정하게 표정을 지어 주게나.",
            'F8': "으음 아무래도 안에 뭐가 있긴 한가 보구만 날 따라오게",
            'F9': "이거 무언가를 거꾸로 말 하는것 같은데, 잠시만 기다려 보게.",
            'F10': "아무래도 자네들에게 필요한 것 같구만. 그 인형은 나한테 주고 가게나, 가지고 다니기엔 위험한 물건이니 나에게 맡기고 가게. 무엇을 쫒고 있는지 모르겠지만 부디 조심하게나.",
        }

        # 펑션키 바인딩 (F1~F10)
        for i in range(1, 11):
            self.root.bind(f'<F{i}>', self.on_function_key)

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
            text="F1~F10: 대사 재생 | Enter: 입력 재생 | ESC: 종료",
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

    def on_function_key(self, event):
        """펑션키로 대본 재생 - 문장 단위로 나눠서 재생"""
        key = event.keysym  # 'F1', 'F2', ...
        if key in self.scripts:
            text = self.scripts[key]
            # 마침표, 물음표, 느낌표 기준으로 문장 분리
            sentences = re.split(r'([.?!])', text)
            # 구분자를 문장에 붙이기
            combined = []
            for i in range(0, len(sentences) - 1, 2):
                combined.append(sentences[i] + sentences[i + 1])
            if len(sentences) % 2 == 1 and sentences[-1].strip():
                combined.append(sentences[-1])
            # 각 문장을 큐에 넣기
            for sentence in combined:
                sentence = sentence.strip()
                if sentence:
                    self.tts_queue.put(sentence)

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
                    # 메인 스레드에서 자막 업데이트
                    self.root.after(0, lambda t=text: self.subtitle_label.config(text=t))
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
