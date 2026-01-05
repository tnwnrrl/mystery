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
import time


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
            'F2': "여기까지 흘러 왔다는건 그만한 이유가 있겠지. 거기 옆에 매고 있는 인형 나한테 줘봐.",
            'F3': "이거 확인을 해 봐야겠는데? 일단 이놈 먼저 처리해야 하는데. 나 좀 도와 주지 않겠나? 그럼 나도 자네들을 도와주지.",
            'F4': "먼저 여기 책상에 있는 표를 보고 주파수를 찾아봐. 주파수를 잘 맞추면 TV 채널을 맞출 수 있을게야.",
            'F5': "덕분에 빨리 봉인할 수 있었네. 나는 인형이나 물건에 깃든 악령이나 사념을 다루는 일을 하고 있다네.",
            'F6': "이 방법으로는 안되겠구만 날 따라오게.",
            'F7': "이 곳은 물건의 사념을 찍을 수 있는 곳이라네. 자네들 앞에 있는 제단에 인형을 올려두고, 마치 가족사진을 찍듯이 다정하게 포즈를 취해주게. 가족같은 느낌이 아니면 사념이 찍히지 않으니, 최대한 다정하게 표정을 지어 주게나.",
            'F8': "아무래도 안에 뭐가 있긴 한가 보구만 날 따라오게",
            'F9': "이거 무언가를 거꾸로 말 하는것 같은데? 잠시만 기다려 보게.",
            'F10': "아무래도 자네들에게 필요한 것 같구만. 그 인형은 나한테 주고 가게나, 가지고 다니기엔 위험한 물건이니 나에게 맡기고 가게. 무엇을 쫒고 있는지 모르겠지만 부디 조심하게나.",
        }

        # 펑션키 바인딩 (F1~F10)
        for i in range(1, 11):
            self.root.bind(f'<F{i}>', self.on_function_key)

        # 화살표로 문장 이동
        self.root.bind('<Left>', self.on_previous_sentence)
        self.root.bind('<Right>', self.on_next_sentence)

        # 재생 상태 관리
        self.is_playing = False
        self.current_sentences = []  # 현재 대사의 문장 리스트
        self.current_index = 0  # 현재 문장 인덱스
        self.current_key = None  # 현재 재생 중인 펑션키
        self.tts_process = None  # 현재 TTS 프로세스

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
            text="F1~F10: 대사 재생 | ←→: 문장 이동 | ESC: 종료",
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

        if self.is_playing:
            if key == self.current_key:
                # 같은 키 → 재생 중지
                self.stop_playback()
                return
            else:
                # 다른 키 → 현재 중지 후 새 재생
                self.stop_playback()

        if key in self.scripts:
            self.current_key = key
            self.play_script(key)

    def stop_playback(self):
        """재생 중지 - 큐 비우기 + TTS 프로세스 종료"""
        # 큐 비우기
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
            except:
                break
        # TTS 프로세스 종료
        if self.tts_process and self.tts_process.poll() is None:
            self.tts_process.terminate()
        self.is_playing = False
        self.current_key = None
        self.subtitle_label.config(text="")

    def on_previous_sentence(self, event):
        """왼쪽 화살표로 이전 문장 재생"""
        if self.is_playing:
            return
        if self.current_sentences and self.current_index > 0:
            self.current_index -= 1
            self.play_single_sentence(self.current_sentences[self.current_index])

    def on_next_sentence(self, event):
        """오른쪽 화살표로 다음 문장 재생"""
        if self.is_playing:
            return
        if self.current_sentences and self.current_index < len(self.current_sentences) - 1:
            self.current_index += 1
            self.play_single_sentence(self.current_sentences[self.current_index])

    def play_single_sentence(self, sentence):
        """단일 문장 재생"""
        self.tts_queue.put(sentence)

    def play_script(self, key):
        """대본 재생 - 문장 분리 후 순차 재생"""
        text = self.scripts[key]

        # 마침표, 물음표, 느낌표 기준으로 문장 분리
        sentences = re.split(r'([.?!])', text)
        # 구분자를 문장에 붙이기
        combined = []
        for i in range(0, len(sentences) - 1, 2):
            combined.append(sentences[i] + sentences[i + 1])
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            combined.append(sentences[-1])

        # 문장 리스트 저장
        self.current_sentences = [s.strip() for s in combined if s.strip()]
        self.current_index = 0

        # 각 문장을 큐에 넣기
        for sentence in self.current_sentences:
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
                self.is_playing = True
                try:
                    # 메인 스레드에서 자막 업데이트
                    self.root.after(0, lambda t=text: self.subtitle_label.config(text=t))
                    self.play_tts(text)
                    # 현재 인덱스 업데이트 (문장 리스트에서 위치 찾기)
                    if text in self.current_sentences:
                        self.current_index = self.current_sentences.index(text)
                    # 문장 사이 딜레이 (0.5초)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"TTS 오류: {e}")
                finally:
                    # 큐가 비었으면 재생 완료
                    if self.tts_queue.empty():
                        self.is_playing = False

    def play_tts(self, text):
        """TTS 음성 재생 - macOS say 명령어 사용 (오프라인)"""
        self.tts_process = subprocess.Popen([
            'say',
            '-v', 'Yuna',  # 한국어 Yuna 음성
            text
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.tts_process.wait()  # 재생 완료 대기

    def run(self):
        """앱 실행"""
        self.root.mainloop()


def main():
    app = KoreanTTSApp()
    app.run()


if __name__ == "__main__":
    main()
