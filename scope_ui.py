"""
Reverse Audio Player - Professional Oscilloscope UI
Using CustomTkinter for modern styling
"""

import customtkinter as ctk
import pygame
from tkinter import filedialog
import numpy as np
import threading
import os
from audio_processor import AudioProcessor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import patches

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class ProfessionalScopeUI:
    # Oscilloscope color scheme
    COLOR_BG = "#000000"
    COLOR_PANEL = "#0a0a0a"
    COLOR_TRACE = "#00ff41"
    COLOR_GRID = "#001a00"
    COLOR_TEXT = "#00ff41"
    COLOR_TEXT_DIM = "#00aa00"
    COLOR_BUTTON = "#003300"
    COLOR_BUTTON_HOVER = "#00ff41"

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("AUDIO SPECTRUM ANALYZER ASA-2000")
        self.root.geometry("1600x950")
        self.root.configure(fg_color=self.COLOR_BG)

        # Audio processor
        self.processor = AudioProcessor()

        # Playback state
        pygame.mixer.init()
        self.is_playing = False
        self.is_paused = False
        self.current_speed = 1.0
        self.temp_audio_file = None

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup professional oscilloscope UI"""

        # ===== HEADER =====
        header = ctk.CTkFrame(self.root, fg_color=self.COLOR_BG, height=80)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="AUDIO SPECTRUM ANALYZER",
            font=("Arial", 36, "bold"),
            text_color=self.COLOR_TRACE
        )
        title.pack(pady=(10, 0))

        subtitle = ctk.CTkLabel(
            header,
            text="MODEL: ASA-2000  |  REVERSE AUDIO ANALYSIS SYSTEM",
            font=("Courier New", 12),
            text_color=self.COLOR_TEXT_DIM
        )
        subtitle.pack(pady=(5, 0))

        # ===== MAIN CONTAINER =====
        main = ctk.CTkFrame(self.root, fg_color=self.COLOR_BG)
        main.pack(fill="both", expand=True, padx=10, pady=5)

        # LEFT PANEL
        self.setup_control_panel(main)

        # RIGHT PANEL
        self.setup_display_panel(main)

        # ===== STATUS BAR =====
        self.setup_status_bar()

    def setup_control_panel(self, parent):
        """Control panel with professional styling"""
        control = ctk.CTkFrame(parent, width=420, fg_color=self.COLOR_PANEL, border_width=2, border_color=self.COLOR_GRID)
        control.pack(side="left", fill="y", padx=(0, 10))
        control.pack_propagate(False)

        # === FILE INPUT ===
        file_frame = self.create_section(control, "FILE INPUT")

        self.file_label = ctk.CTkLabel(
            file_frame,
            text="NO SIGNAL",
            font=("Courier New", 13, "bold"),
            text_color=self.COLOR_TEXT_DIM,
            wraplength=360
        )
        self.file_label.pack(pady=15)

        load_btn = ctk.CTkButton(
            file_frame,
            text="LOAD FILE",
            command=self.load_file,
            font=("Courier New", 14, "bold"),
            fg_color=self.COLOR_BUTTON,
            hover_color=self.COLOR_TRACE,
            text_color=self.COLOR_TRACE,
            border_width=2,
            border_color=self.COLOR_TRACE,
            height=45,
            width=320
        )
        load_btn.pack(pady=10)

        # === SIGNAL PROCESSOR ===
        processor_frame = self.create_section(control, "SIGNAL PROCESSOR")

        reverse_btn = ctk.CTkButton(
            processor_frame,
            text="⟲ REVERSE SIGNAL",
            command=self.reverse_audio,
            font=("Courier New", 14, "bold"),
            fg_color=self.COLOR_BUTTON,
            hover_color="#ffff00",
            text_color="#ffff00",
            border_width=2,
            border_color="#ffff00",
            height=45,
            width=320
        )
        reverse_btn.pack(pady=10)

        self.reverse_status = ctk.CTkLabel(
            processor_frame,
            text="⚫ STANDBY",
            font=("Courier New", 13, "bold"),
            text_color=self.COLOR_TEXT_DIM
        )
        self.reverse_status.pack(pady=10)

        # === SIGNAL PARAMETERS ===
        params_frame = self.create_section(control, "SIGNAL PARAMETERS")

        params_grid = ctk.CTkFrame(params_frame, fg_color=self.COLOR_PANEL)
        params_grid.pack(padx=15, pady=15, fill="both")

        self.param_labels = {}
        parameters = [
            ("Fs", "N/A", "Hz"),
            ("CH", "N/A", ""),
            ("BITS", "N/A", "bit"),
            ("RATE", "N/A", "kbps"),
            ("TIME", "N/A", "s"),
            ("FMT", "N/A", "")
        ]

        for i, (name, default, unit) in enumerate(parameters):
            row = i // 2
            col = i % 2

            param = ctk.CTkFrame(params_grid, fg_color="#000000", border_width=2, border_color=self.COLOR_GRID)
            param.grid(row=row, column=col, padx=8, pady=8, sticky="ew")

            label = ctk.CTkLabel(
                param,
                text=name,
                font=("Courier New", 10),
                text_color=self.COLOR_TEXT_DIM
            )
            label.pack(anchor="w", padx=8, pady=(5, 2))

            value = ctk.CTkLabel(
                param,
                text=f"{default} {unit}",
                font=("Courier New", 16, "bold"),
                text_color=self.COLOR_TRACE
            )
            value.pack(anchor="w", padx=8, pady=(0, 5))

            self.param_labels[name] = value

        # === PLAYBACK ===
        playback_frame = self.create_section(control, "PLAYBACK CONTROL")

        button_grid = ctk.CTkFrame(playback_frame, fg_color=self.COLOR_PANEL)
        button_grid.pack(pady=15)

        self.play_btn = ctk.CTkButton(
            button_grid,
            text="▶ PLAY",
            command=self.play_audio,
            font=("Courier New", 13, "bold"),
            fg_color=self.COLOR_BUTTON,
            hover_color=self.COLOR_TRACE,
            text_color=self.COLOR_TRACE,
            border_width=2,
            border_color=self.COLOR_TRACE,
            width=150,
            height=40
        )
        self.play_btn.grid(row=0, column=0, padx=5, pady=5)

        self.pause_btn = ctk.CTkButton(
            button_grid,
            text="❚❚ PAUSE",
            command=self.pause_audio,
            font=("Courier New", 13, "bold"),
            fg_color=self.COLOR_BUTTON,
            hover_color=self.COLOR_TRACE,
            text_color=self.COLOR_TRACE,
            border_width=2,
            border_color=self.COLOR_TRACE,
            width=150,
            height=40
        )
        self.pause_btn.grid(row=0, column=1, padx=5, pady=5)

        self.stop_btn = ctk.CTkButton(
            button_grid,
            text="■ STOP",
            command=self.stop_audio,
            font=("Courier New", 13, "bold"),
            fg_color=self.COLOR_BUTTON,
            hover_color="#ff0000",
            text_color="#ff0000",
            border_width=2,
            border_color="#ff0000",
            width=310,
            height=40
        )
        self.stop_btn.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        # === TIMEBASE ===
        timebase_frame = self.create_section(control, "TIMEBASE CONTROL")

        speed_display = ctk.CTkFrame(timebase_frame, fg_color="#000000", border_width=3, border_color=self.COLOR_GRID)
        speed_display.pack(pady=15, padx=20, fill="x")

        self.speed_label = ctk.CTkLabel(
            speed_display,
            text="1.00x",
            font=("Courier New", 28, "bold"),
            text_color=self.COLOR_TRACE
        )
        self.speed_label.pack(pady=15)

        self.speed_slider = ctk.CTkSlider(
            timebase_frame,
            from_=0.5,
            to=2.0,
            number_of_steps=15,
            command=self.on_speed_change,
            fg_color=self.COLOR_GRID,
            progress_color=self.COLOR_TRACE,
            button_color=self.COLOR_TRACE,
            button_hover_color=self.COLOR_BUTTON_HOVER,
            width=340,
            height=20
        )
        self.speed_slider.set(1.0)
        self.speed_slider.pack(pady=10, padx=20)

        # Speed markers
        markers = ctk.CTkFrame(timebase_frame, fg_color=self.COLOR_PANEL)
        markers.pack(fill="x", padx=30)

        for speed in ["0.5x", "1.0x", "1.5x", "2.0x"]:
            ctk.CTkLabel(
                markers,
                text=speed,
                font=("Courier New", 9),
                text_color=self.COLOR_TEXT_DIM
            ).pack(side="left", expand=True)

    def setup_display_panel(self, parent):
        """Oscilloscope display panel"""
        display = ctk.CTkFrame(parent, fg_color=self.COLOR_BG, border_width=2, border_color=self.COLOR_GRID)
        display.pack(side="left", fill="both", expand=True)

        # === CHANNEL 1 ===
        ch1_label = ctk.CTkLabel(
            display,
            text="CH1: TIME DOMAIN WAVEFORM",
            font=("Courier New", 14, "bold"),
            text_color=self.COLOR_TRACE
        )
        ch1_label.pack(pady=(15, 5))

        # Waveform
        self.waveform_fig = Figure(figsize=(12, 3.8), facecolor=self.COLOR_BG)
        self.waveform_ax = self.waveform_fig.add_subplot(111)
        self.waveform_ax.set_facecolor(self.COLOR_BG)

        self.waveform_canvas = FigureCanvasTkAgg(self.waveform_fig, display)
        self.waveform_canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.style_scope_axis(self.waveform_ax, "TIME (ms)", "AMPLITUDE (V)")

        # === CHANNEL 2 ===
        ch2_label = ctk.CTkLabel(
            display,
            text="CH2: FREQUENCY DOMAIN SPECTRUM",
            font=("Courier New", 14, "bold"),
            text_color=self.COLOR_TRACE
        )
        ch2_label.pack(pady=(10, 5))

        # Spectrum
        self.spectrum_fig = Figure(figsize=(12, 3.8), facecolor=self.COLOR_BG)
        self.spectrum_ax = self.spectrum_fig.add_subplot(111)
        self.spectrum_ax.set_facecolor(self.COLOR_BG)

        self.spectrum_canvas = FigureCanvasTkAgg(self.spectrum_fig, display)
        self.spectrum_canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.style_scope_axis(self.spectrum_ax, "FREQUENCY (Hz)", "MAGNITUDE (dB)")

    def setup_status_bar(self):
        """Status bar"""
        status = ctk.CTkFrame(self.root, fg_color=self.COLOR_PANEL, height=40, border_width=2, border_color=self.COLOR_GRID)
        status.pack(fill="x", side="bottom", padx=10, pady=10)
        status.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            status,
            text="⚫ SYSTEM READY",
            font=("Courier New", 12, "bold"),
            text_color=self.COLOR_TRACE
        )
        self.status_label.pack(side="left", padx=20)

        self.time_label = ctk.CTkLabel(
            status,
            text="00:00.000",
            font=("Courier New", 12, "bold"),
            text_color=self.COLOR_TRACE
        )
        self.time_label.pack(side="right", padx=20)

    def create_section(self, parent, title):
        """Create labeled section"""
        section = ctk.CTkFrame(parent, fg_color=self.COLOR_PANEL, border_width=2, border_color=self.COLOR_GRID)
        section.pack(fill="x", padx=10, pady=10)

        label = ctk.CTkLabel(
            section,
            text=f"═══ {title} ═══",
            font=("Courier New", 12, "bold"),
            text_color=self.COLOR_TRACE
        )
        label.pack(pady=(10, 5))

        return section

    def style_scope_axis(self, ax, xlabel, ylabel):
        """Style matplotlib axis as oscilloscope"""
        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.grid(True, which="major", color=self.COLOR_GRID, linewidth=1.5, alpha=0.8)
        ax.grid(True, which="minor", color=self.COLOR_GRID, linewidth=0.5, alpha=0.4)
        ax.minorticks_on()

        ax.tick_params(colors=self.COLOR_TEXT_DIM, which="both", labelsize=9)
        ax.set_xlabel(xlabel, color=self.COLOR_TEXT_DIM, fontsize=10, weight="bold")
        ax.set_ylabel(ylabel, color=self.COLOR_TEXT_DIM, fontsize=10, weight="bold")

        rect = patches.Rectangle(
            (0, 0), 1, 1,
            transform=ax.transAxes,
            fill=False,
            edgecolor=self.COLOR_GRID,
            linewidth=2
        )
        ax.add_patch(rect)

    def update_status(self, message, color=None):
        """Update status"""
        if color is None:
            color = self.COLOR_TRACE
        self.status_label.configure(text=f"● {message}", text_color=color)

    def load_file(self):
        """Load audio file"""
        file_path = filedialog.askopenfilename(
            title="SELECT AUDIO FILE",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav"),
                ("MP3 Files", "*.mp3"),
                ("WAV Files", "*.wav")
            ]
        )

        if file_path:
            try:
                self.update_status("LOADING SIGNAL...", "#ffff00")

                self.processor.load_audio(file_path)

                filename = os.path.basename(file_path)
                self.file_label.configure(text=filename, text_color=self.COLOR_TRACE)
                self.update_status(f"SIGNAL ACQUIRED", self.COLOR_TRACE)

                self.update_parameters()
                self.draw_waveform()
                self.draw_spectrum()

            except Exception as e:
                self.update_status(f"ERROR: {str(e)}", "#ff0000")
                self.file_label.configure(text="LOAD FAILED", text_color="#ff0000")

    def reverse_audio(self):
        """Reverse audio"""
        if self.processor.audio is None:
            self.update_status("ERROR: NO SIGNAL", "#ff0000")
            return

        try:
            self.update_status("PROCESSING...", "#ffff00")
            self.reverse_status.configure(text="⚫ PROCESSING", text_color="#ffff00")

            def reverse_thread():
                self.processor.reverse_audio()
                self.root.after(0, self.on_reverse_complete)

            thread = threading.Thread(target=reverse_thread, daemon=True)
            thread.start()

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", "#ff0000")
            self.reverse_status.configure(text="⚫ FAILED", text_color="#ff0000")

    def on_reverse_complete(self):
        """Reverse complete"""
        self.reverse_status.configure(text="● REVERSED", text_color=self.COLOR_TRACE)
        self.update_status("SIGNAL REVERSED", self.COLOR_TRACE)
        self.draw_waveform()
        self.draw_spectrum()

    def play_audio(self):
        """Play audio"""
        if self.processor.reversed_audio is None:
            self.update_status("ERROR: NO REVERSED SIGNAL", "#ff0000")
            return

        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.update_status("PLAYBACK ACTIVE", self.COLOR_TRACE)
            else:
                audio_to_play = self.processor.change_speed(self.current_speed)

                if self.temp_audio_file:
                    try:
                        os.remove(self.temp_audio_file)
                    except:
                        pass

                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                self.temp_audio_file = temp_file.name
                temp_file.close()

                audio_to_play.export(self.temp_audio_file, format="wav")
                pygame.mixer.music.load(self.temp_audio_file)
                pygame.mixer.music.play()

                self.is_playing = True
                self.update_status(f"PLAYING @ {self.current_speed:.2f}x", self.COLOR_TRACE)

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", "#ff0000")

    def pause_audio(self):
        """Pause"""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.update_status("PAUSED", "#ffff00")

    def stop_audio(self):
        """Stop"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.update_status("STOPPED", "#ff0000")

    def on_speed_change(self, value):
        """Speed change"""
        self.current_speed = float(value)
        self.speed_label.configure(text=f"{self.current_speed:.2f}x")

        if self.is_playing and not self.is_paused:
            self.stop_audio()
            self.play_audio()

    def update_parameters(self):
        """Update parameter displays"""
        metadata = self.processor.get_metadata()
        if metadata:
            self.param_labels["Fs"].configure(text=f"{metadata['sample_rate']} Hz")
            self.param_labels["CH"].configure(text=f"{metadata['channels']}")
            self.param_labels["BITS"].configure(text=f"{metadata['bit_depth']} bit")
            self.param_labels["RATE"].configure(text=f"{metadata['bitrate']:.0f} kbps")
            self.param_labels["TIME"].configure(text=f"{metadata['duration']:.2f} s")
            self.param_labels["FMT"].configure(text=f"{metadata['format']}")

    def draw_waveform(self):
        """Draw waveform"""
        self.waveform_ax.clear()

        audio_data = self.processor.get_audio_data()
        if audio_data is None:
            self.style_scope_axis(self.waveform_ax, "TIME (ms)", "AMPLITUDE (V)")
            self.waveform_ax.text(
                0.5, 0.5, "NO SIGNAL",
                ha="center", va="center",
                transform=self.waveform_ax.transAxes,
                color=self.COLOR_TEXT_DIM,
                fontsize=18,
                weight="bold"
            )
            self.waveform_canvas.draw()
            return

        if len(audio_data.shape) > 1:
            samples = audio_data[:, 0]
        else:
            samples = audio_data

        display_samples = 4000
        if len(samples) > display_samples:
            step = len(samples) // display_samples
            samples = samples[::step]

        samples = samples / (np.max(np.abs(samples)) + 1e-10)

        duration_ms = self.processor.duration_ms
        time_ms = np.linspace(0, duration_ms, len(samples))

        # Glow effect
        self.waveform_ax.plot(time_ms, samples, color=self.COLOR_TRACE, linewidth=4, alpha=0.3)
        self.waveform_ax.plot(time_ms, samples, color=self.COLOR_TRACE, linewidth=2, alpha=0.6)
        self.waveform_ax.plot(time_ms, samples, color=self.COLOR_TRACE, linewidth=1, alpha=1.0)

        self.waveform_ax.set_xlim(0, duration_ms)
        self.waveform_ax.set_ylim(-1.2, 1.2)
        self.style_scope_axis(self.waveform_ax, "TIME (ms)", "AMPLITUDE (V)")

        self.waveform_ax.axhline(y=0, color=self.COLOR_GRID, linewidth=1.5, alpha=0.8)

        self.waveform_canvas.draw()

    def draw_spectrum(self):
        """Draw spectrum"""
        self.spectrum_ax.clear()

        audio_data = self.processor.get_audio_data()
        if audio_data is None:
            self.style_scope_axis(self.spectrum_ax, "FREQUENCY (Hz)", "MAGNITUDE (dB)")
            self.spectrum_ax.text(
                0.5, 0.5, "NO SIGNAL",
                ha="center", va="center",
                transform=self.spectrum_ax.transAxes,
                color=self.COLOR_TEXT_DIM,
                fontsize=18,
                weight="bold"
            )
            self.spectrum_canvas.draw()
            return

        if len(audio_data.shape) > 1:
            samples = audio_data[:, 0]
        else:
            samples = audio_data

        fft_size = min(16384, len(samples))
        chunk = samples[:fft_size]

        fft = np.fft.fft(chunk)
        freqs = np.fft.fftfreq(len(chunk), 1.0 / self.processor.sample_rate)

        positive_freqs = freqs[:len(freqs)//2]
        magnitude = np.abs(fft[:len(fft)//2])

        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        magnitude_db = magnitude_db - np.min(magnitude_db)

        from scipy import signal
        window_size = 51
        if len(magnitude_db) > window_size:
            magnitude_db = signal.savgol_filter(magnitude_db, window_size, 3)

        # Glow effect
        self.spectrum_ax.plot(positive_freqs, magnitude_db, color=self.COLOR_TRACE, linewidth=4, alpha=0.3)
        self.spectrum_ax.plot(positive_freqs, magnitude_db, color=self.COLOR_TRACE, linewidth=2, alpha=0.6)
        self.spectrum_ax.plot(positive_freqs, magnitude_db, color=self.COLOR_TRACE, linewidth=1, alpha=1.0)

        self.spectrum_ax.fill_between(positive_freqs, magnitude_db, 0, color=self.COLOR_TRACE, alpha=0.2)

        self.spectrum_ax.set_xlim(20, self.processor.sample_rate/2)
        self.spectrum_ax.set_xscale("log")
        self.style_scope_axis(self.spectrum_ax, "FREQUENCY (Hz)", "MAGNITUDE (dB)")

        self.spectrum_canvas.draw()

    def run(self):
        """Run application"""
        self.root.mainloop()

        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
            except:
                pass


if __name__ == "__main__":
    app = ProfessionalScopeUI()
    app.run()
