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
import json
import os

def get_secondary_monitor():
    """보조 모니터 정보 반환 (없으면 None)"""
    try:
        # system_profiler로 디스플레이 정보 가져오기
        result = subprocess.run(
            ['system_profiler', 'SPDisplaysDataType', '-json'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            import json as json_module
            data = json_module.loads(result.stdout)
            displays = []
            for gpu in data.get('SPDisplaysDataType', []):
                for display in gpu.get('spdisplays_ndrvs', []):
                    # "_spdisplays_pixels" 필드 사용 (예: "1920 x 1080")
                    res = display.get('_spdisplays_pixels', '')
                    if ' x ' in res:
                        parts = res.split(' x ')
                        if len(parts) == 2:
                            w = int(parts[0].strip())
                            h = int(parts[1].strip())
                            is_main = display.get('spdisplays_main') == 'spdisplays_yes'
                            displays.append({'width': w, 'height': h, 'is_main': is_main})

            # 메인이 아닌 디스플레이 찾기
            for d in displays:
                if not d['is_main']:
                    # 보조 모니터는 메인 오른쪽에 있음 (x = 메인너비)
                    main_width = next((x['width'] for x in displays if x['is_main']), 0)
                    return {
                        'x': main_width,
                        'y': 0,
                        'width': d['width'],
                        'height': d['height']
                    }
    except Exception:
        pass
    return None


class KoreanTTSApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("한글 TTS 자막")

        # 보조 모니터 감지
        secondary = get_secondary_monitor()

        if secondary:
            # 보조 모니터에 전체화면 (fullscreen 사용)
            screen_width = secondary['width']
            self.root.geometry(f"+{secondary['x']}+{secondary['y']}")
            self.root.attributes('-fullscreen', True)
        else:
            # 메인 모니터에 전체화면
            self.root.attributes('-fullscreen', True)
            screen_width = self.root.winfo_screenwidth()

        self.root.configure(bg='black')

        # ESC 키로 종료
        self.root.bind('<Escape>', lambda e: self.root.quit())

        # 대본 로드 (scripts.json)
        self.scripts = self.load_scripts()

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
            wraplength=screen_width - 100
        )
        self.subtitle_label.place(relx=0.5, rely=0.5, anchor='center')

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

    def get_function_keys(self):
        """사용 가능한 F키 목록 (정렬된 순서)"""
        return sorted(self.scripts.keys(), key=lambda x: int(x[1:]))

    def split_sentences(self, text):
        """텍스트를 문장 단위로 분리"""
        sentences = re.split(r'([.?!])', text)
        combined = []
        for i in range(0, len(sentences) - 1, 2):
            combined.append(sentences[i] + sentences[i + 1])
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            combined.append(sentences[-1])
        return [s.strip() for s in combined if s.strip()]

    def on_previous_sentence(self, event):
        """왼쪽 화살표로 이전 문장 재생 (F키 간 이동 포함)"""
        if self.is_playing:
            return

        if self.current_sentences and self.current_index > 0:
            # 같은 F키 내에서 이전 문장
            self.current_index -= 1
            self.play_single_sentence(self.current_sentences[self.current_index])
        elif self.current_key:
            # 이전 F키로 이동
            keys = self.get_function_keys()
            current_idx = keys.index(self.current_key) if self.current_key in keys else -1
            if current_idx > 0:
                prev_key = keys[current_idx - 1]
                self.current_key = prev_key
                self.current_sentences = self.split_sentences(self.scripts[prev_key])
                self.current_index = len(self.current_sentences) - 1  # 마지막 문장
                if self.current_sentences:
                    self.play_single_sentence(self.current_sentences[self.current_index])

    def on_next_sentence(self, event):
        """오른쪽 화살표로 다음 문장 재생 (F키 간 이동 포함)"""
        if self.is_playing:
            return

        if self.current_sentences and self.current_index < len(self.current_sentences) - 1:
            # 같은 F키 내에서 다음 문장
            self.current_index += 1
            self.play_single_sentence(self.current_sentences[self.current_index])
        elif self.current_key:
            # 다음 F키로 이동
            keys = self.get_function_keys()
            current_idx = keys.index(self.current_key) if self.current_key in keys else -1
            if current_idx < len(keys) - 1:
                next_key = keys[current_idx + 1]
                self.current_key = next_key
                self.current_sentences = self.split_sentences(self.scripts[next_key])
                self.current_index = 0  # 첫 문장
                if self.current_sentences:
                    self.play_single_sentence(self.current_sentences[self.current_index])

    def play_single_sentence(self, sentence):
        """단일 문장 재생"""
        self.tts_queue.put(sentence)

    def play_script(self, key):
        """대본 재생 - 문장 분리 후 순차 재생"""
        self.current_sentences = self.split_sentences(self.scripts[key])
        self.current_index = 0

        # 각 문장을 큐에 넣기
        for sentence in self.current_sentences:
            self.tts_queue.put(sentence)

    def cleanup_entry(self):
        """Entry 정리 - IME 조합이 없을 때만"""
        # Entry를 비우고 sent_text도 리셋
        self.entry_var.set("")
        self.sent_text = ""

    def load_scripts(self):
        """scripts.json에서 대본 로드"""
        script_path = os.path.join(os.path.dirname(__file__), 'scripts.json')
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"경고: {script_path} 파일을 찾을 수 없습니다. 기본 대본을 사용합니다.")
            return {f'F{i}': f"F{i} 대본이 설정되지 않았습니다." for i in range(1, 11)}
        except json.JSONDecodeError as e:
            print(f"경고: scripts.json 파싱 오류: {e}")
            return {f'F{i}': f"F{i} 대본이 설정되지 않았습니다." for i in range(1, 11)}

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
