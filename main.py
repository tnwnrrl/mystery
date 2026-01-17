"""
Reverse Audio Player - Cyberpunk Edition
Main GUI Application (macOS compatible - no pygame)
"""

import subprocess
import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import threading
import os
import sys
from audio_processor import AudioProcessor


class CyberpunkAudioPlayer:
    # Cyberpunk color scheme
    COLOR_BG = '#0a0e27'
    COLOR_BG_DARK = '#050811'
    COLOR_ACCENT = '#00ff9f'
    COLOR_ACCENT_DIM = '#00cc7f'
    COLOR_TEXT = '#e0e0e0'
    COLOR_TEXT_DIM = '#808080'
    COLOR_DANGER = '#ff0055'
    COLOR_WARNING = '#ffaa00'
    COLOR_PANEL = '#151b3d'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("◢ REVERSE AUDIO ANALYZER ◣")
        self.root.geometry("1200x800")
        self.root.configure(bg=self.COLOR_BG)
        self.root.resizable(True, True)

        # Audio processor
        self.processor = AudioProcessor()

        # Playback state (using afplay)
        self.play_process = None
        self.is_playing = False
        self.is_paused = False
        self.current_speed = 1.0
        self.temp_audio_file = None

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the main UI"""
        # Title bar
        title_frame = tk.Frame(self.root, bg=self.COLOR_BG, height=60)
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        title_label = tk.Label(
            title_frame,
            text="◢ REVERSE AUDIO ANALYZER v2.0 ◣",
            font=('Consolas', 24, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_ACCENT
        )
        title_label.pack(side=tk.LEFT)

        subtitle_label = tk.Label(
            title_frame,
            text="[ AUDIO MANIPULATION SYSTEM ]",
            font=('Consolas', 10),
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT_DIM
        )
        subtitle_label.pack(side=tk.LEFT, padx=20)

        # Main container
        main_container = tk.Frame(self.root, bg=self.COLOR_BG)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left panel - Controls
        self.setup_control_panel(main_container)

        # Right panel - Visualization & Metrics
        self.setup_visualization_panel(main_container)

        # Bottom status bar
        self.setup_status_bar()

    def setup_control_panel(self, parent):
        """Setup control panel on the left"""
        control_frame = tk.Frame(parent, bg=self.COLOR_PANEL, width=350)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)

        # File selection section
        file_section = tk.LabelFrame(
            control_frame,
            text="▼ FILE LOADER",
            font=('Consolas', 12, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_ACCENT,
            relief=tk.FLAT,
            borderwidth=2
        )
        file_section.pack(fill=tk.X, padx=15, pady=15)

        self.file_label = tk.Label(
            file_section,
            text="[ NO FILE LOADED ]",
            font=('Consolas', 10),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXT_DIM,
            wraplength=300
        )
        self.file_label.pack(pady=10)

        load_btn = self.create_cyber_button(
            file_section,
            text="◢ LOAD AUDIO FILE ◣",
            command=self.load_file
        )
        load_btn.pack(pady=10)

        # Reverse section
        reverse_section = tk.LabelFrame(
            control_frame,
            text="▼ AUDIO PROCESSOR",
            font=('Consolas', 12, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_ACCENT,
            relief=tk.FLAT,
            borderwidth=2
        )
        reverse_section.pack(fill=tk.X, padx=15, pady=15)

        reverse_btn = self.create_cyber_button(
            reverse_section,
            text="◢ REVERSE AUDIO ◣",
            command=self.reverse_audio,
            color=self.COLOR_WARNING
        )
        reverse_btn.pack(pady=10)

        self.reverse_status = tk.Label(
            reverse_section,
            text="[ READY TO PROCESS ]",
            font=('Consolas', 9),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXT_DIM
        )
        self.reverse_status.pack(pady=5)

        # Playback controls section
        playback_section = tk.LabelFrame(
            control_frame,
            text="▼ PLAYBACK CONTROLS",
            font=('Consolas', 12, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_ACCENT,
            relief=tk.FLAT,
            borderwidth=2
        )
        playback_section.pack(fill=tk.X, padx=15, pady=15)

        # Play/Pause/Stop buttons
        btn_frame = tk.Frame(playback_section, bg=self.COLOR_PANEL)
        btn_frame.pack(pady=10)

        self.play_btn = self.create_cyber_button(
            btn_frame,
            text="▶ PLAY",
            command=self.play_audio,
            width=8
        )
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.pause_btn = self.create_cyber_button(
            btn_frame,
            text="▮▮ PAUSE",
            command=self.pause_audio,
            width=8
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = self.create_cyber_button(
            btn_frame,
            text="■ STOP",
            command=self.stop_audio,
            width=8,
            color=self.COLOR_DANGER
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Speed control
        speed_frame = tk.Frame(playback_section, bg=self.COLOR_PANEL)
        speed_frame.pack(pady=10, fill=tk.X, padx=10)

        speed_label = tk.Label(
            speed_frame,
            text="SPEED MULTIPLIER:",
            font=('Consolas', 9),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXT
        )
        speed_label.pack()

        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = tk.Scale(
            speed_frame,
            from_=0.5,
            to=2.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            command=self.on_speed_change,
            bg=self.COLOR_PANEL,
            fg=self.COLOR_ACCENT,
            troughcolor=self.COLOR_BG_DARK,
            highlightthickness=0,
            font=('Consolas', 8)
        )
        self.speed_scale.pack(fill=tk.X, pady=5)

        self.speed_display = tk.Label(
            speed_frame,
            text="[ 1.0x ]",
            font=('Consolas', 10, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_ACCENT
        )
        self.speed_display.pack()

    def setup_visualization_panel(self, parent):
        """Setup visualization and metrics panel on the right"""
        viz_frame = tk.Frame(parent, bg=self.COLOR_BG)
        viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Metrics panel
        metrics_section = tk.LabelFrame(
            viz_frame,
            text="▼ TECHNICAL METRICS",
            font=('Consolas', 12, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_ACCENT,
            relief=tk.FLAT,
            borderwidth=2
        )
        metrics_section.pack(fill=tk.X, pady=(0, 10))

        # Create metrics grid
        metrics_container = tk.Frame(metrics_section, bg=self.COLOR_PANEL)
        metrics_container.pack(padx=20, pady=15)

        self.metric_labels = {}
        metrics = [
            ('FORMAT', 'N/A'),
            ('SAMPLE RATE', 'N/A'),
            ('CHANNELS', 'N/A'),
            ('BIT DEPTH', 'N/A'),
            ('BITRATE', 'N/A'),
            ('DURATION', 'N/A')
        ]

        for i, (label, default) in enumerate(metrics):
            row = i // 3
            col = i % 3

            metric_frame = tk.Frame(metrics_container, bg=self.COLOR_PANEL)
            metric_frame.grid(row=row, column=col, padx=15, pady=10, sticky='w')

            label_widget = tk.Label(
                metric_frame,
                text=f"{label}:",
                font=('Consolas', 9),
                bg=self.COLOR_PANEL,
                fg=self.COLOR_TEXT_DIM
            )
            label_widget.pack(anchor='w')

            value_widget = tk.Label(
                metric_frame,
                text=default,
                font=('Consolas', 11, 'bold'),
                bg=self.COLOR_PANEL,
                fg=self.COLOR_ACCENT
            )
            value_widget.pack(anchor='w')

            self.metric_labels[label] = value_widget

        # Waveform visualization placeholder
        waveform_section = tk.LabelFrame(
            viz_frame,
            text="▼ WAVEFORM ANALYSIS",
            font=('Consolas', 12, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_ACCENT,
            relief=tk.FLAT,
            borderwidth=2
        )
        waveform_section.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.waveform_canvas = tk.Canvas(
            waveform_section,
            bg=self.COLOR_BG_DARK,
            highlightthickness=0
        )
        self.waveform_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Spectrum analyzer placeholder
        spectrum_section = tk.LabelFrame(
            viz_frame,
            text="▼ FREQUENCY SPECTRUM",
            font=('Consolas', 12, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_ACCENT,
            relief=tk.FLAT,
            borderwidth=2
        )
        spectrum_section.pack(fill=tk.BOTH, expand=True)

        self.spectrum_canvas = tk.Canvas(
            spectrum_section,
            bg=self.COLOR_BG_DARK,
            highlightthickness=0
        )
        self.spectrum_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def setup_status_bar(self):
        """Setup status bar at the bottom"""
        status_frame = tk.Frame(self.root, bg=self.COLOR_BG_DARK, height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(
            status_frame,
            text="[ SYSTEM READY ]",
            font=('Consolas', 9),
            bg=self.COLOR_BG_DARK,
            fg=self.COLOR_ACCENT,
            anchor='w'
        )
        self.status_label.pack(side=tk.LEFT, padx=20, pady=5)

    def create_cyber_button(self, parent, text, command, width=20, color=None):
        """Create a cyberpunk-styled button"""
        if color is None:
            color = self.COLOR_ACCENT

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=('Consolas', 10, 'bold'),
            bg=self.COLOR_BG_DARK,
            fg=color,
            activebackground=color,
            activeforeground=self.COLOR_BG_DARK,
            relief=tk.FLAT,
            borderwidth=2,
            width=width,
            cursor='hand2'
        )

        # Hover effects
        def on_enter(e):
            btn['bg'] = color
            btn['fg'] = self.COLOR_BG_DARK

        def on_leave(e):
            btn['bg'] = self.COLOR_BG_DARK
            btn['fg'] = color

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)

        return btn

    def update_status(self, message, color=None):
        """Update status bar message"""
        if color is None:
            color = self.COLOR_ACCENT
        self.status_label.config(text=f"[ {message} ]", fg=color)

    def load_file(self):
        """Load audio file"""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav"),
                ("MP3 Files", "*.mp3"),
                ("WAV Files", "*.wav"),
                ("All Files", "*.*")
            ]
        )

        if file_path:
            try:
                self.update_status("LOADING FILE...", self.COLOR_WARNING)
                self.processor.load_audio(file_path)

                filename = os.path.basename(file_path)
                self.file_label.config(text=f"[ {filename} ]", fg=self.COLOR_ACCENT)
                self.update_status(f"FILE LOADED: {filename}", self.COLOR_ACCENT)

                # Update metrics
                self.update_metrics()

                # Draw initial waveform
                self.draw_waveform()
                self.draw_spectrum()

            except Exception as e:
                self.update_status(f"ERROR: {str(e)}", self.COLOR_DANGER)
                self.file_label.config(text="[ LOAD FAILED ]", fg=self.COLOR_DANGER)

    def reverse_audio(self):
        """Reverse the loaded audio"""
        if self.processor.audio is None:
            self.update_status("ERROR: NO AUDIO LOADED", self.COLOR_DANGER)
            return

        try:
            self.update_status("REVERSING AUDIO...", self.COLOR_WARNING)
            self.reverse_status.config(text="[ PROCESSING... ]", fg=self.COLOR_WARNING)

            # Reverse in separate thread to avoid UI freeze
            def reverse_thread():
                self.processor.reverse_audio()
                self.root.after(0, self.on_reverse_complete)

            thread = threading.Thread(target=reverse_thread)
            thread.start()

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", self.COLOR_DANGER)
            self.reverse_status.config(text="[ FAILED ]", fg=self.COLOR_DANGER)

    def on_reverse_complete(self):
        """Called when reverse operation completes"""
        self.reverse_status.config(text="[ REVERSED ✓ ]", fg=self.COLOR_ACCENT)
        self.update_status("AUDIO REVERSED SUCCESSFULLY", self.COLOR_ACCENT)

        # Update visualizations with reversed audio
        self.draw_waveform()
        self.draw_spectrum()

    def play_audio(self):
        """Play the reversed audio using afplay"""
        if self.processor.reversed_audio is None:
            self.update_status("ERROR: NO REVERSED AUDIO AVAILABLE", self.COLOR_DANGER)
            return

        try:
            # Stop any existing playback
            self.stop_audio()

            # Export to temp file with current speed
            audio_to_play = self.processor.change_speed(self.current_speed)

            if self.temp_audio_file:
                try:
                    os.remove(self.temp_audio_file)
                except:
                    pass

            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            self.temp_audio_file = temp_file.name
            temp_file.close()

            audio_to_play.export(self.temp_audio_file, format='wav')

            # Play using afplay (macOS)
            self.play_process = subprocess.Popen(
                ['afplay', self.temp_audio_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self.is_playing = True
            self.is_paused = False
            self.update_status(f"PLAYING (SPEED: {self.current_speed}x)", self.COLOR_ACCENT)

            # Monitor playback in background
            def monitor_playback():
                if self.play_process:
                    self.play_process.wait()
                    if self.is_playing:
                        self.root.after(0, lambda: self.update_status("PLAYBACK FINISHED", self.COLOR_ACCENT))
                        self.is_playing = False

            thread = threading.Thread(target=monitor_playback, daemon=True)
            thread.start()

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", self.COLOR_DANGER)

    def pause_audio(self):
        """Pause/Resume playback"""
        if self.play_process and self.is_playing:
            if not self.is_paused:
                # Pause by sending SIGSTOP
                self.play_process.send_signal(subprocess.signal.SIGSTOP)
                self.is_paused = True
                self.update_status("PLAYBACK PAUSED", self.COLOR_WARNING)
            else:
                # Resume by sending SIGCONT
                self.play_process.send_signal(subprocess.signal.SIGCONT)
                self.is_paused = False
                self.update_status(f"PLAYING (SPEED: {self.current_speed}x)", self.COLOR_ACCENT)

    def stop_audio(self):
        """Stop playback"""
        if self.play_process:
            try:
                self.play_process.terminate()
                self.play_process.wait(timeout=1)
            except:
                try:
                    self.play_process.kill()
                except:
                    pass
            self.play_process = None

        self.is_playing = False
        self.is_paused = False
        self.update_status("PLAYBACK STOPPED", self.COLOR_DANGER)

    def on_speed_change(self, value):
        """Handle speed slider change"""
        self.current_speed = float(value)
        self.speed_display.config(text=f"[ {self.current_speed:.1f}x ]")

        # If currently playing, restart with new speed
        if self.is_playing and not self.is_paused:
            self.play_audio()

    def update_metrics(self):
        """Update technical metrics display"""
        metadata = self.processor.get_metadata()
        if metadata:
            self.metric_labels['FORMAT'].config(text=metadata['format'])
            self.metric_labels['SAMPLE RATE'].config(text=f"{metadata['sample_rate']} Hz")
            self.metric_labels['CHANNELS'].config(text=f"{metadata['channels']}")
            self.metric_labels['BIT DEPTH'].config(text=f"{metadata['bit_depth']} bit")
            self.metric_labels['BITRATE'].config(text=f"{metadata['bitrate']:.0f} kbps")
            self.metric_labels['DURATION'].config(text=f"{metadata['duration']:.2f} sec")

    def draw_waveform(self):
        """Draw waveform visualization"""
        self.waveform_canvas.delete('all')

        audio_data = self.processor.get_audio_data()
        if audio_data is None:
            return

        # Get canvas dimensions
        width = self.waveform_canvas.winfo_width()
        height = self.waveform_canvas.winfo_height()

        if width < 10 or height < 10:
            # Canvas not yet properly sized, schedule redraw
            self.root.after(100, self.draw_waveform)
            return

        # Downsample for display
        if len(audio_data.shape) > 1:
            # Stereo - use first channel
            samples = audio_data[:, 0]
        else:
            samples = audio_data

        display_samples = 2000
        if len(samples) > display_samples:
            step = len(samples) // display_samples
            samples = samples[::step]

        # Normalize
        samples = samples / (np.max(np.abs(samples)) + 1e-10)

        # Draw grid
        for i in range(5):
            y = height * i / 4
            self.waveform_canvas.create_line(
                0, y, width, y,
                fill=self.COLOR_BG,
                width=1
            )

        # Draw waveform
        center_y = height / 2
        x_step = width / len(samples)

        points = []
        for i, sample in enumerate(samples):
            x = i * x_step
            y = center_y - (sample * center_y * 0.9)
            points.append((x, y))

        # Draw as connected lines
        for i in range(len(points) - 1):
            self.waveform_canvas.create_line(
                points[i][0], points[i][1],
                points[i+1][0], points[i+1][1],
                fill=self.COLOR_ACCENT,
                width=1
            )

        # Draw center line
        self.waveform_canvas.create_line(
            0, center_y, width, center_y,
            fill=self.COLOR_ACCENT_DIM,
            width=2
        )

    def draw_spectrum(self):
        """Draw frequency spectrum visualization"""
        self.spectrum_canvas.delete('all')

        audio_data = self.processor.get_audio_data()
        if audio_data is None:
            return

        # Get canvas dimensions
        width = self.spectrum_canvas.winfo_width()
        height = self.spectrum_canvas.winfo_height()

        if width < 10 or height < 10:
            # Canvas not yet properly sized, schedule redraw
            self.root.after(100, self.draw_spectrum)
            return

        # Get samples for FFT
        if len(audio_data.shape) > 1:
            samples = audio_data[:, 0]
        else:
            samples = audio_data

        # Take a chunk for FFT
        fft_size = min(8192, len(samples))
        chunk = samples[:fft_size]

        # Compute FFT
        fft = np.fft.fft(chunk)
        freqs = np.fft.fftfreq(len(chunk), 1.0 / self.processor.sample_rate)

        # Take only positive frequencies
        positive_freqs = freqs[:len(freqs)//2]
        magnitude = np.abs(fft[:len(fft)//2])

        # Convert to dB scale
        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        magnitude_db = magnitude_db - np.min(magnitude_db)
        magnitude_db = magnitude_db / (np.max(magnitude_db) + 1e-10)

        # Draw spectrum bars
        num_bars = 60
        bar_width = width / num_bars

        # Logarithmic frequency binning
        freq_bins = np.logspace(np.log10(20), np.log10(self.processor.sample_rate/2), num_bars)

        for i in range(num_bars):
            # Find magnitude in this frequency range
            if i < len(freq_bins) - 1:
                freq_mask = (positive_freqs >= freq_bins[i]) & (positive_freqs < freq_bins[i+1])
                if np.any(freq_mask):
                    bar_height = np.mean(magnitude_db[freq_mask]) * height * 0.9
                else:
                    bar_height = 0
            else:
                bar_height = 0

            x1 = i * bar_width
            x2 = x1 + bar_width - 2
            y1 = height - bar_height
            y2 = height

            # Color gradient based on frequency
            color_factor = i / num_bars
            if color_factor < 0.5:
                # Low freq - more green
                color = self.COLOR_ACCENT
            else:
                # High freq - more cyan
                color = '#00ffff'

            self.spectrum_canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color,
                outline=''
            )

    def run(self):
        """Run the application"""
        # Bind resize event for visualizations
        self.waveform_canvas.bind('<Configure>', lambda e: self.draw_waveform())
        self.spectrum_canvas.bind('<Configure>', lambda e: self.draw_spectrum())

        self.root.mainloop()

        # Cleanup
        self.stop_audio()
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
            except:
                pass


if __name__ == "__main__":
    app = CyberpunkAudioPlayer()
    app.run()
