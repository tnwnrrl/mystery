"""
Reverse Audio Player - Oscilloscope Edition
Real measurement equipment aesthetic
"""

import pygame
import tkinter as tk
from tkinter import filedialog
import numpy as np
import threading
import os
from audio_processor import AudioProcessor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import patches


class OscilloscopeAudioPlayer:
    # Oscilloscope color scheme (classic CRT phosphor green)
    COLOR_BG = '#000000'  # Pure black
    COLOR_GRID = '#001a00'  # Very dark green
    COLOR_TRACE = '#00ff41'  # Bright phosphor green
    COLOR_TRACE_GLOW = '#00ff41'  # Glow effect
    COLOR_TEXT = '#00ff41'  # Green text
    COLOR_TEXT_DIM = '#006600'  # Dim green
    COLOR_PANEL = '#0a0a0a'  # Almost black
    COLOR_BUTTON = '#001a00'  # Dark green
    COLOR_BUTTON_ACTIVE = '#00ff41'  # Bright green
    COLOR_WARNING = '#ffff00'  # Yellow
    COLOR_DANGER = '#ff0000'  # Red

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OSCILLOSCOPE AUDIO ANALYZER")
        self.root.geometry("1600x900")
        self.root.configure(bg=self.COLOR_BG)

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
        """Setup oscilloscope-style UI"""
        # ===== TOP PANEL - Equipment Header =====
        header_frame = tk.Frame(self.root, bg=self.COLOR_BG, height=70)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        # Equipment label
        equipment_label = tk.Label(
            header_frame,
            text="AUDIO SPECTRUM ANALYZER",
            font=('Arial', 32, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_TRACE
        )
        equipment_label.pack(side=tk.TOP)

        model_label = tk.Label(
            header_frame,
            text="MODEL: ASA-2000 | REVERSE AUDIO ANALYSIS SYSTEM",
            font=('Courier New', 11),
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT_DIM
        )
        model_label.pack(side=tk.TOP, pady=5)

        # ===== MAIN CONTAINER =====
        main_container = tk.Frame(self.root, bg=self.COLOR_BG)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # LEFT PANEL - Controls and Meters
        self.setup_control_panel(main_container)

        # RIGHT PANEL - Oscilloscope Display
        self.setup_scope_panel(main_container)

        # ===== BOTTOM STATUS =====
        self.setup_status_bar()

    def setup_control_panel(self, parent):
        """Control panel with measurement displays"""
        control_frame = tk.Frame(parent, bg=self.COLOR_PANEL, width=400, relief=tk.RIDGE, borderwidth=3)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)

        # === FILE INPUT SECTION ===
        file_section = self.create_scope_section(control_frame, "FILE INPUT")

        self.file_label = tk.Label(
            file_section,
            text="NO SIGNAL",
            font=('Courier New', 11, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXT_DIM,
            wraplength=350,
            justify=tk.CENTER
        )
        self.file_label.pack(pady=15)

        load_btn = self.create_scope_button(
            file_section,
            text="LOAD FILE",
            command=self.load_file
        )
        load_btn.pack(pady=10)

        # === SIGNAL PROCESSOR ===
        processor_section = self.create_scope_section(control_frame, "SIGNAL PROCESSOR")

        reverse_btn = self.create_scope_button(
            processor_section,
            text="REVERSE",
            command=self.reverse_audio,
            color=self.COLOR_WARNING
        )
        reverse_btn.pack(pady=10)

        self.reverse_status = tk.Label(
            processor_section,
            text="STANDBY",
            font=('Courier New', 12, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXT_DIM
        )
        self.reverse_status.pack(pady=8)

        # === VU METERS / TECHNICAL READOUTS ===
        meters_section = self.create_scope_section(control_frame, "SIGNAL PARAMETERS")

        meters_grid = tk.Frame(meters_section, bg=self.COLOR_PANEL)
        meters_grid.pack(padx=20, pady=15, fill=tk.BOTH, expand=True)

        self.meter_labels = {}
        meter_params = [
            ('Fs', 'N/A', 'Hz'),
            ('CH', 'N/A', ''),
            ('BITS', 'N/A', 'bit'),
            ('RATE', 'N/A', 'kbps'),
            ('TIME', 'N/A', 's'),
            ('FMT', 'N/A', '')
        ]

        for i, (label, default, unit) in enumerate(meter_params):
            row = i // 2
            col = i % 2

            meter_frame = tk.Frame(meters_grid, bg=self.COLOR_PANEL, relief=tk.SUNKEN, borderwidth=2)
            meter_frame.grid(row=row, column=col, padx=8, pady=8, sticky='ew')

            lbl = tk.Label(
                meter_frame,
                text=label,
                font=('Courier New', 9),
                bg=self.COLOR_PANEL,
                fg=self.COLOR_TEXT_DIM
            )
            lbl.pack(anchor='w', padx=5, pady=2)

            val_frame = tk.Frame(meter_frame, bg=self.COLOR_BG)
            val_frame.pack(fill=tk.X, padx=5, pady=3)

            val = tk.Label(
                val_frame,
                text=f"{default}",
                font=('Courier New', 14, 'bold'),
                bg=self.COLOR_BG,
                fg=self.COLOR_TRACE
            )
            val.pack(side=tk.LEFT)

            if unit:
                unit_lbl = tk.Label(
                    val_frame,
                    text=f" {unit}",
                    font=('Courier New', 9),
                    bg=self.COLOR_BG,
                    fg=self.COLOR_TEXT_DIM
                )
                unit_lbl.pack(side=tk.LEFT)

            self.meter_labels[label] = val

        # === PLAYBACK CONTROLS ===
        playback_section = self.create_scope_section(control_frame, "PLAYBACK")

        btn_grid = tk.Frame(playback_section, bg=self.COLOR_PANEL)
        btn_grid.pack(pady=15)

        self.play_btn = self.create_scope_button(
            btn_grid,
            text="▶ PLAY",
            command=self.play_audio,
            width=10
        )
        self.play_btn.grid(row=0, column=0, padx=5, pady=5)

        self.pause_btn = self.create_scope_button(
            btn_grid,
            text="║ PAUSE",
            command=self.pause_audio,
            width=10
        )
        self.pause_btn.grid(row=0, column=1, padx=5, pady=5)

        self.stop_btn = self.create_scope_button(
            btn_grid,
            text="■ STOP",
            command=self.stop_audio,
            width=10,
            color=self.COLOR_DANGER
        )
        self.stop_btn.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='ew')

        # === SPEED CONTROL ===
        speed_section = self.create_scope_section(control_frame, "TIMEBASE")

        speed_display_frame = tk.Frame(speed_section, bg=self.COLOR_BG, relief=tk.SUNKEN, borderwidth=3)
        speed_display_frame.pack(pady=10, padx=20, fill=tk.X)

        self.speed_display = tk.Label(
            speed_display_frame,
            text="1.00x",
            font=('Courier New', 24, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_TRACE
        )
        self.speed_display.pack(pady=10)

        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = tk.Scale(
            speed_section,
            from_=0.5,
            to=2.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            command=self.on_speed_change,
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TRACE,
            troughcolor=self.COLOR_BG,
            highlightthickness=0,
            font=('Courier New', 8),
            length=300,
            width=20
        )
        self.speed_scale.pack(fill=tk.X, padx=20, pady=10)

        # Speed markers
        speed_markers = tk.Frame(speed_section, bg=self.COLOR_PANEL)
        speed_markers.pack(fill=tk.X, padx=25)

        for speed in ['0.5x', '1.0x', '1.5x', '2.0x']:
            tk.Label(
                speed_markers,
                text=speed,
                font=('Courier New', 8),
                bg=self.COLOR_PANEL,
                fg=self.COLOR_TEXT_DIM
            ).pack(side=tk.LEFT, expand=True)

    def setup_scope_panel(self, parent):
        """Oscilloscope display panel"""
        scope_frame = tk.Frame(parent, bg=self.COLOR_BG, relief=tk.RIDGE, borderwidth=3)
        scope_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # === CHANNEL 1 - WAVEFORM ===
        ch1_label = tk.Label(
            scope_frame,
            text="CH1: TIME DOMAIN",
            font=('Courier New', 12, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_TRACE
        )
        ch1_label.pack(pady=(10, 5))

        # Waveform display
        self.waveform_fig = Figure(figsize=(12, 3.5), facecolor=self.COLOR_BG)
        self.waveform_ax = self.waveform_fig.add_subplot(111)
        self.waveform_ax.set_facecolor(self.COLOR_BG)

        self.waveform_canvas = FigureCanvasTkAgg(self.waveform_fig, scope_frame)
        self.waveform_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.style_scope_axis(self.waveform_ax, 'TIME (ms)', 'AMPLITUDE (V)')

        # === CHANNEL 2 - SPECTRUM ===
        ch2_label = tk.Label(
            scope_frame,
            text="CH2: FREQUENCY DOMAIN",
            font=('Courier New', 12, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_TRACE
        )
        ch2_label.pack(pady=(10, 5))

        # Spectrum display
        self.spectrum_fig = Figure(figsize=(12, 3.5), facecolor=self.COLOR_BG)
        self.spectrum_ax = self.spectrum_fig.add_subplot(111)
        self.spectrum_ax.set_facecolor(self.COLOR_BG)

        self.spectrum_canvas = FigureCanvasTkAgg(self.spectrum_fig, scope_frame)
        self.spectrum_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.style_scope_axis(self.spectrum_ax, 'FREQUENCY (Hz)', 'MAGNITUDE (dB)')

    def setup_status_bar(self):
        """Status bar"""
        status_frame = tk.Frame(self.root, bg=self.COLOR_BG, relief=tk.RIDGE, borderwidth=2)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(5, 10))

        self.status_label = tk.Label(
            status_frame,
            text="SYSTEM READY",
            font=('Courier New', 11, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_TRACE,
            anchor='w'
        )
        self.status_label.pack(side=tk.LEFT, padx=15, pady=8)

        # Time display
        self.time_label = tk.Label(
            status_frame,
            text="00:00.000",
            font=('Courier New', 11, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_TRACE,
            anchor='e'
        )
        self.time_label.pack(side=tk.RIGHT, padx=15, pady=8)

    def create_scope_section(self, parent, title):
        """Create oscilloscope-style section"""
        section = tk.LabelFrame(
            parent,
            text=f"  {title}  ",
            font=('Courier New', 10, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TRACE,
            relief=tk.RIDGE,
            borderwidth=2
        )
        section.pack(fill=tk.X, padx=10, pady=8)
        return section

    def create_scope_button(self, parent, text, command, width=15, color=None):
        """Create oscilloscope-style button"""
        if color is None:
            color = self.COLOR_TRACE

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=('Courier New', 11, 'bold'),
            bg=self.COLOR_BUTTON,
            fg=color,
            activebackground=color,
            activeforeground=self.COLOR_BG,
            relief=tk.RAISED,
            borderwidth=3,
            width=width,
            cursor='hand2'
        )

        def on_enter(e):
            btn['bg'] = color
            btn['fg'] = self.COLOR_BG

        def on_leave(e):
            btn['bg'] = self.COLOR_BUTTON
            btn['fg'] = color

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)

        return btn

    def style_scope_axis(self, ax, xlabel, ylabel):
        """Apply oscilloscope styling to axis"""
        # Remove default spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Create grid like oscilloscope
        ax.grid(True, which='major', color=self.COLOR_GRID, linewidth=1.5, alpha=0.8)
        ax.grid(True, which='minor', color=self.COLOR_GRID, linewidth=0.5, alpha=0.4)
        ax.minorticks_on()

        # Style ticks and labels
        ax.tick_params(colors=self.COLOR_TEXT_DIM, which='both', labelsize=9)
        ax.set_xlabel(xlabel, color=self.COLOR_TEXT_DIM, fontsize=10, weight='bold')
        ax.set_ylabel(ylabel, color=self.COLOR_TEXT_DIM, fontsize=10, weight='bold')

        # Draw border
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
        self.status_label.config(text=message, fg=color)

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
                self.update_status("LOADING SIGNAL...", self.COLOR_WARNING)

                self.processor.load_audio(file_path)

                filename = os.path.basename(file_path)
                self.file_label.config(text=filename, fg=self.COLOR_TRACE)
                self.update_status(f"SIGNAL ACQUIRED: {filename}", self.COLOR_TRACE)

                self.update_meters()
                self.draw_waveform()
                self.draw_spectrum()

            except Exception as e:
                self.update_status(f"ERROR: {str(e)}", self.COLOR_DANGER)
                self.file_label.config(text="LOAD FAILED", fg=self.COLOR_DANGER)

    def reverse_audio(self):
        """Reverse audio"""
        if self.processor.audio is None:
            self.update_status("ERROR: NO SIGNAL", self.COLOR_DANGER)
            return

        try:
            self.update_status("PROCESSING...", self.COLOR_WARNING)
            self.reverse_status.config(text="PROCESSING", fg=self.COLOR_WARNING)

            def reverse_thread():
                self.processor.reverse_audio()
                self.root.after(0, self.on_reverse_complete)

            thread = threading.Thread(target=reverse_thread, daemon=True)
            thread.start()

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", self.COLOR_DANGER)
            self.reverse_status.config(text="FAILED", fg=self.COLOR_DANGER)

    def on_reverse_complete(self):
        """Reverse complete callback"""
        self.reverse_status.config(text="REVERSED", fg=self.COLOR_TRACE)
        self.update_status("SIGNAL REVERSED", self.COLOR_TRACE)

        self.draw_waveform()
        self.draw_spectrum()

    def play_audio(self):
        """Play audio"""
        if self.processor.reversed_audio is None:
            self.update_status("ERROR: NO REVERSED SIGNAL", self.COLOR_DANGER)
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
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                self.temp_audio_file = temp_file.name
                temp_file.close()

                audio_to_play.export(self.temp_audio_file, format='wav')
                pygame.mixer.music.load(self.temp_audio_file)
                pygame.mixer.music.play()

                self.is_playing = True
                self.update_status(f"PLAYBACK @ {self.current_speed}x", self.COLOR_TRACE)

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", self.COLOR_DANGER)

    def pause_audio(self):
        """Pause playback"""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.update_status("PAUSED", self.COLOR_WARNING)

    def stop_audio(self):
        """Stop playback"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.update_status("STOPPED", self.COLOR_DANGER)

    def on_speed_change(self, value):
        """Speed change handler"""
        self.current_speed = float(value)
        self.speed_display.config(text=f"{self.current_speed:.2f}x")

        if self.is_playing and not self.is_paused:
            self.stop_audio()
            self.play_audio()

    def update_meters(self):
        """Update technical meters"""
        metadata = self.processor.get_metadata()
        if metadata:
            self.meter_labels['Fs'].config(text=f"{metadata['sample_rate']}")
            self.meter_labels['CH'].config(text=f"{metadata['channels']}")
            self.meter_labels['BITS'].config(text=f"{metadata['bit_depth']}")
            self.meter_labels['RATE'].config(text=f"{metadata['bitrate']:.0f}")
            self.meter_labels['TIME'].config(text=f"{metadata['duration']:.2f}")
            self.meter_labels['FMT'].config(text=f"{metadata['format']}")

    def draw_waveform(self):
        """Draw oscilloscope waveform"""
        self.waveform_ax.clear()

        audio_data = self.processor.get_audio_data()
        if audio_data is None:
            self.style_scope_axis(self.waveform_ax, 'TIME (ms)', 'AMPLITUDE (V)')
            self.waveform_ax.text(
                0.5, 0.5, 'NO SIGNAL',
                ha='center', va='center',
                transform=self.waveform_ax.transAxes,
                color=self.COLOR_TEXT_DIM,
                fontsize=16,
                weight='bold'
            )
            self.waveform_canvas.draw()
            return

        # Get samples
        if len(audio_data.shape) > 1:
            samples = audio_data[:, 0]
        else:
            samples = audio_data

        # Downsample
        display_samples = 4000
        if len(samples) > display_samples:
            step = len(samples) // display_samples
            samples = samples[::step]

        # Normalize
        samples = samples / (np.max(np.abs(samples)) + 1e-10)

        # Time axis
        duration_ms = self.processor.duration_ms
        time_ms = np.linspace(0, duration_ms, len(samples))

        # Draw trace with glow effect
        # Outer glow
        self.waveform_ax.plot(
            time_ms, samples,
            color=self.COLOR_TRACE_GLOW,
            linewidth=4,
            alpha=0.3
        )
        # Middle glow
        self.waveform_ax.plot(
            time_ms, samples,
            color=self.COLOR_TRACE_GLOW,
            linewidth=2,
            alpha=0.6
        )
        # Core trace
        self.waveform_ax.plot(
            time_ms, samples,
            color=self.COLOR_TRACE,
            linewidth=1,
            alpha=1.0
        )

        # Style
        self.waveform_ax.set_xlim(0, duration_ms)
        self.waveform_ax.set_ylim(-1.2, 1.2)
        self.style_scope_axis(self.waveform_ax, 'TIME (ms)', 'AMPLITUDE (V)')

        # Center line
        self.waveform_ax.axhline(y=0, color=self.COLOR_GRID, linewidth=1.5, alpha=0.8)

        self.waveform_canvas.draw()

    def draw_spectrum(self):
        """Draw oscilloscope spectrum"""
        self.spectrum_ax.clear()

        audio_data = self.processor.get_audio_data()
        if audio_data is None:
            self.style_scope_axis(self.spectrum_ax, 'FREQUENCY (Hz)', 'MAGNITUDE (dB)')
            self.spectrum_ax.text(
                0.5, 0.5, 'NO SIGNAL',
                ha='center', va='center',
                transform=self.spectrum_ax.transAxes,
                color=self.COLOR_TEXT_DIM,
                fontsize=16,
                weight='bold'
            )
            self.spectrum_canvas.draw()
            return

        # Get samples
        if len(audio_data.shape) > 1:
            samples = audio_data[:, 0]
        else:
            samples = audio_data

        # FFT
        fft_size = min(16384, len(samples))
        chunk = samples[:fft_size]

        fft = np.fft.fft(chunk)
        freqs = np.fft.fftfreq(len(chunk), 1.0 / self.processor.sample_rate)

        # Positive frequencies
        positive_freqs = freqs[:len(freqs)//2]
        magnitude = np.abs(fft[:len(fft)//2])

        # Convert to dB
        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        magnitude_db = magnitude_db - np.min(magnitude_db)

        # Smooth
        from scipy import signal
        window_size = 51
        if len(magnitude_db) > window_size:
            magnitude_db = signal.savgol_filter(magnitude_db, window_size, 3)

        # Plot with glow effect
        # Outer glow
        self.spectrum_ax.plot(
            positive_freqs, magnitude_db,
            color=self.COLOR_TRACE_GLOW,
            linewidth=4,
            alpha=0.3
        )
        # Middle glow
        self.spectrum_ax.plot(
            positive_freqs, magnitude_db,
            color=self.COLOR_TRACE_GLOW,
            linewidth=2,
            alpha=0.6
        )
        # Core trace
        self.spectrum_ax.plot(
            positive_freqs, magnitude_db,
            color=self.COLOR_TRACE,
            linewidth=1,
            alpha=1.0
        )

        # Fill
        self.spectrum_ax.fill_between(
            positive_freqs, magnitude_db, 0,
            color=self.COLOR_TRACE,
            alpha=0.2
        )

        # Style
        self.spectrum_ax.set_xlim(20, self.processor.sample_rate/2)
        self.spectrum_ax.set_xscale('log')
        self.style_scope_axis(self.spectrum_ax, 'FREQUENCY (Hz)', 'MAGNITUDE (dB)')

        self.spectrum_canvas.draw()

    def run(self):
        """Run application"""
        self.root.mainloop()

        # Cleanup
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
            except:
                pass


if __name__ == "__main__":
    app = OscilloscopeAudioPlayer()
    app.run()
