"""
Reverse Audio Player - Enhanced Cyberpunk Edition
Main GUI Application with Real-time Visualization
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
import matplotlib.animation as animation
from matplotlib import style


class EnhancedCyberpunkPlayer:
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
    COLOR_CYAN = '#00ffff'
    COLOR_PURPLE = '#9d4edd'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("◢◤ REVERSE AUDIO ANALYZER ◥◣")
        self.root.geometry("1400x900")
        self.root.configure(bg=self.COLOR_BG)

        # Set matplotlib style
        plt.style.use('dark_background')

        # Audio processor
        self.processor = AudioProcessor()

        # Playback state
        pygame.mixer.init()
        self.is_playing = False
        self.is_paused = False
        self.current_speed = 1.0
        self.temp_audio_file = None

        # Animation state
        self.animation_running = False

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup enhanced UI with real visualizations"""
        # ===== TITLE BAR =====
        title_frame = tk.Frame(self.root, bg=self.COLOR_BG, height=80)
        title_frame.pack(fill=tk.X, padx=20, pady=(15, 5))

        # Main title with glow effect
        title_label = tk.Label(
            title_frame,
            text="◢◤ REVERSE AUDIO ANALYZER ◥◣",
            font=('Courier New', 28, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_ACCENT
        )
        title_label.pack(side=tk.TOP)

        subtitle_label = tk.Label(
            title_frame,
            text="[ ADVANCED AUDIO MANIPULATION SYSTEM v2.0 ]",
            font=('Courier New', 11),
            bg=self.COLOR_BG,
            fg=self.COLOR_CYAN
        )
        subtitle_label.pack(side=tk.TOP, pady=5)

        # Status indicators
        indicator_frame = tk.Frame(title_frame, bg=self.COLOR_BG)
        indicator_frame.pack(side=tk.TOP, pady=5)

        self.system_status = tk.Label(
            indicator_frame,
            text="● SYSTEM ONLINE",
            font=('Courier New', 9),
            bg=self.COLOR_BG,
            fg=self.COLOR_ACCENT
        )
        self.system_status.pack(side=tk.LEFT, padx=10)

        self.audio_status = tk.Label(
            indicator_frame,
            text="● AUDIO ENGINE READY",
            font=('Courier New', 9),
            bg=self.COLOR_BG,
            fg=self.COLOR_ACCENT
        )
        self.audio_status.pack(side=tk.LEFT, padx=10)

        # ===== MAIN CONTAINER =====
        main_container = tk.Frame(self.root, bg=self.COLOR_BG)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # LEFT PANEL - Controls
        self.setup_control_panel(main_container)

        # RIGHT PANEL - Visualizations
        self.setup_visualization_panel(main_container)

        # ===== BOTTOM STATUS BAR =====
        self.setup_status_bar()

    def setup_control_panel(self, parent):
        """Enhanced control panel"""
        control_frame = tk.Frame(parent, bg=self.COLOR_PANEL, width=380)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        control_frame.pack_propagate(False)

        # === FILE SECTION ===
        file_section = self.create_section(control_frame, "◢ FILE LOADER ◣")

        self.file_label = tk.Label(
            file_section,
            text="[ NO FILE LOADED ]",
            font=('Courier New', 10),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXT_DIM,
            wraplength=330,
            justify=tk.LEFT
        )
        self.file_label.pack(pady=10, padx=10)

        load_btn = self.create_neon_button(
            file_section,
            text="◢ LOAD AUDIO FILE ◣",
            command=self.load_file,
            color=self.COLOR_ACCENT
        )
        load_btn.pack(pady=10)

        # === PROCESSOR SECTION ===
        processor_section = self.create_section(control_frame, "◢ AUDIO PROCESSOR ◣")

        reverse_btn = self.create_neon_button(
            processor_section,
            text="◢ REVERSE AUDIO ◣",
            command=self.reverse_audio,
            color=self.COLOR_WARNING
        )
        reverse_btn.pack(pady=10)

        self.reverse_status = tk.Label(
            processor_section,
            text="[ READY TO PROCESS ]",
            font=('Courier New', 10, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXT_DIM
        )
        self.reverse_status.pack(pady=5)

        # === TECHNICAL METRICS ===
        metrics_section = self.create_section(control_frame, "◢ TECHNICAL METRICS ◣")

        metrics_container = tk.Frame(metrics_section, bg=self.COLOR_PANEL)
        metrics_container.pack(padx=15, pady=10, fill=tk.BOTH)

        self.metric_labels = {}
        metrics_data = [
            ('FORMAT', 'N/A'),
            ('SAMPLE RATE', 'N/A'),
            ('CHANNELS', 'N/A'),
            ('BIT DEPTH', 'N/A'),
            ('BITRATE', 'N/A'),
            ('DURATION', 'N/A')
        ]

        for i, (label, default) in enumerate(metrics_data):
            row = i // 2
            col = i % 2

            frame = tk.Frame(metrics_container, bg=self.COLOR_PANEL)
            frame.grid(row=row, column=col, padx=10, pady=8, sticky='w')

            lbl = tk.Label(
                frame,
                text=f"{label}:",
                font=('Courier New', 8),
                bg=self.COLOR_PANEL,
                fg=self.COLOR_TEXT_DIM
            )
            lbl.pack(anchor='w')

            val = tk.Label(
                frame,
                text=default,
                font=('Courier New', 11, 'bold'),
                bg=self.COLOR_PANEL,
                fg=self.COLOR_ACCENT
            )
            val.pack(anchor='w')

            self.metric_labels[label] = val

        # === PLAYBACK SECTION ===
        playback_section = self.create_section(control_frame, "◢ PLAYBACK CONTROLS ◣")

        # Buttons
        btn_container = tk.Frame(playback_section, bg=self.COLOR_PANEL)
        btn_container.pack(pady=15)

        self.play_btn = self.create_neon_button(
            btn_container,
            text="▶ PLAY",
            command=self.play_audio,
            width=9,
            color=self.COLOR_ACCENT
        )
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.pause_btn = self.create_neon_button(
            btn_container,
            text="❚❚ PAUSE",
            command=self.pause_audio,
            width=9,
            color=self.COLOR_CYAN
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = self.create_neon_button(
            btn_container,
            text="■ STOP",
            command=self.stop_audio,
            width=9,
            color=self.COLOR_DANGER
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Speed control
        speed_frame = tk.Frame(playback_section, bg=self.COLOR_PANEL)
        speed_frame.pack(pady=10, fill=tk.X, padx=20)

        speed_label = tk.Label(
            speed_frame,
            text="◢ SPEED MULTIPLIER ◣",
            font=('Courier New', 10, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_ACCENT
        )
        speed_label.pack(pady=5)

        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = tk.Scale(
            speed_frame,
            from_=0.5,
            to=2.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            command=self.on_speed_change,
            bg=self.COLOR_BG_DARK,
            fg=self.COLOR_ACCENT,
            troughcolor=self.COLOR_BG,
            highlightthickness=0,
            font=('Courier New', 9),
            length=300
        )
        self.speed_scale.pack(fill=tk.X, pady=5)

        self.speed_display = tk.Label(
            speed_frame,
            text="[ 1.0x ]",
            font=('Courier New', 14, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_ACCENT
        )
        self.speed_display.pack(pady=5)

    def setup_visualization_panel(self, parent):
        """Enhanced visualization panel with matplotlib"""
        viz_frame = tk.Frame(parent, bg=self.COLOR_BG)
        viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # === WAVEFORM SECTION ===
        waveform_section = self.create_section(viz_frame, "◢ WAVEFORM ANALYSIS ◣", False)
        waveform_section.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create matplotlib figure for waveform
        self.waveform_fig = Figure(figsize=(10, 3), facecolor=self.COLOR_BG_DARK)
        self.waveform_ax = self.waveform_fig.add_subplot(111)
        self.waveform_ax.set_facecolor(self.COLOR_BG_DARK)

        self.waveform_canvas = FigureCanvasTkAgg(self.waveform_fig, waveform_section)
        self.waveform_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.style_axis(self.waveform_ax)
        self.waveform_ax.set_xlabel('TIME (ms)', color=self.COLOR_ACCENT, fontsize=9)
        self.waveform_ax.set_ylabel('AMPLITUDE', color=self.COLOR_ACCENT, fontsize=9)
        self.waveform_ax.grid(True, alpha=0.2, color=self.COLOR_ACCENT)

        # === SPECTRUM SECTION ===
        spectrum_section = self.create_section(viz_frame, "◢ FREQUENCY SPECTRUM ◣", False)
        spectrum_section.pack(fill=tk.BOTH, expand=True)

        # Create matplotlib figure for spectrum
        self.spectrum_fig = Figure(figsize=(10, 3), facecolor=self.COLOR_BG_DARK)
        self.spectrum_ax = self.spectrum_fig.add_subplot(111)
        self.spectrum_ax.set_facecolor(self.COLOR_BG_DARK)

        self.spectrum_canvas = FigureCanvasTkAgg(self.spectrum_fig, spectrum_section)
        self.spectrum_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.style_axis(self.spectrum_ax)
        self.spectrum_ax.set_xlabel('FREQUENCY (Hz)', color=self.COLOR_ACCENT, fontsize=9)
        self.spectrum_ax.set_ylabel('MAGNITUDE (dB)', color=self.COLOR_ACCENT, fontsize=9)
        self.spectrum_ax.grid(True, alpha=0.2, color=self.COLOR_ACCENT)
        self.spectrum_ax.set_xscale('log')

    def setup_status_bar(self):
        """Status bar"""
        status_frame = tk.Frame(self.root, bg=self.COLOR_BG_DARK, height=35)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(
            status_frame,
            text="[ SYSTEM INITIALIZED - READY FOR OPERATION ]",
            font=('Courier New', 10),
            bg=self.COLOR_BG_DARK,
            fg=self.COLOR_ACCENT,
            anchor='w'
        )
        self.status_label.pack(side=tk.LEFT, padx=20, pady=8)

    def create_section(self, parent, title, pack_propagate=True):
        """Create a labeled section frame"""
        section = tk.LabelFrame(
            parent,
            text=title,
            font=('Courier New', 11, 'bold'),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_ACCENT,
            relief=tk.RIDGE,
            borderwidth=2,
            labelanchor='n'
        )
        if pack_propagate:
            section.pack(fill=tk.X, padx=15, pady=12)
        return section

    def create_neon_button(self, parent, text, command, width=20, color=None):
        """Create neon-styled button with hover effects"""
        if color is None:
            color = self.COLOR_ACCENT

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=('Courier New', 11, 'bold'),
            bg=self.COLOR_BG_DARK,
            fg=color,
            activebackground=color,
            activeforeground=self.COLOR_BG_DARK,
            relief=tk.RAISED,
            borderwidth=3,
            width=width,
            cursor='hand2'
        )

        def on_enter(e):
            btn['bg'] = color
            btn['fg'] = self.COLOR_BG_DARK
            btn['relief'] = tk.SUNKEN

        def on_leave(e):
            btn['bg'] = self.COLOR_BG_DARK
            btn['fg'] = color
            btn['relief'] = tk.RAISED

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)

        return btn

    def style_axis(self, ax):
        """Apply cyberpunk styling to matplotlib axis"""
        ax.spines['bottom'].set_color(self.COLOR_ACCENT)
        ax.spines['top'].set_color(self.COLOR_ACCENT)
        ax.spines['left'].set_color(self.COLOR_ACCENT)
        ax.spines['right'].set_color(self.COLOR_ACCENT)
        ax.tick_params(colors=self.COLOR_ACCENT, which='both')

    def update_status(self, message, color=None):
        """Update status bar"""
        if color is None:
            color = self.COLOR_ACCENT
        self.status_label.config(text=f"[ {message} ]", fg=color)

    def load_file(self):
        """Load audio file with enhanced feedback"""
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
                self.update_status("LOADING FILE...", self.COLOR_WARNING)
                self.audio_status.config(text="● LOADING...", fg=self.COLOR_WARNING)

                self.processor.load_audio(file_path)

                filename = os.path.basename(file_path)
                self.file_label.config(
                    text=f"◢ LOADED ◣\n{filename}",
                    fg=self.COLOR_ACCENT
                )
                self.update_status(f"FILE LOADED: {filename}", self.COLOR_ACCENT)
                self.audio_status.config(text="● AUDIO LOADED", fg=self.COLOR_ACCENT)

                # Update metrics
                self.update_metrics()

                # Draw visualizations
                self.draw_waveform()
                self.draw_spectrum()

            except Exception as e:
                self.update_status(f"ERROR: {str(e)}", self.COLOR_DANGER)
                self.file_label.config(text="[ LOAD FAILED ]", fg=self.COLOR_DANGER)
                self.audio_status.config(text="● ERROR", fg=self.COLOR_DANGER)

    def reverse_audio(self):
        """Reverse audio with enhanced feedback"""
        if self.processor.audio is None:
            self.update_status("ERROR: NO AUDIO LOADED", self.COLOR_DANGER)
            return

        try:
            self.update_status("REVERSING AUDIO...", self.COLOR_WARNING)
            self.reverse_status.config(text="[ PROCESSING... ]", fg=self.COLOR_WARNING)
            self.audio_status.config(text="● PROCESSING...", fg=self.COLOR_WARNING)

            def reverse_thread():
                self.processor.reverse_audio()
                self.root.after(0, self.on_reverse_complete)

            thread = threading.Thread(target=reverse_thread, daemon=True)
            thread.start()

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", self.COLOR_DANGER)
            self.reverse_status.config(text="[ FAILED ]", fg=self.COLOR_DANGER)

    def on_reverse_complete(self):
        """Callback when reverse completes"""
        self.reverse_status.config(text="[ ✓ REVERSED ]", fg=self.COLOR_ACCENT)
        self.update_status("AUDIO REVERSED SUCCESSFULLY", self.COLOR_ACCENT)
        self.audio_status.config(text="● REVERSED READY", fg=self.COLOR_ACCENT)

        # Update visualizations
        self.draw_waveform()
        self.draw_spectrum()

    def play_audio(self):
        """Play reversed audio"""
        if self.processor.reversed_audio is None:
            self.update_status("ERROR: NO REVERSED AUDIO", self.COLOR_DANGER)
            return

        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.update_status("PLAYBACK RESUMED", self.COLOR_ACCENT)
                self.audio_status.config(text="● PLAYING", fg=self.COLOR_ACCENT)
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
                self.update_status(f"PLAYING @ {self.current_speed}x SPEED", self.COLOR_ACCENT)
                self.audio_status.config(text="● PLAYING", fg=self.COLOR_ACCENT)

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", self.COLOR_DANGER)

    def pause_audio(self):
        """Pause playback"""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.update_status("PLAYBACK PAUSED", self.COLOR_WARNING)
            self.audio_status.config(text="● PAUSED", fg=self.COLOR_WARNING)

    def stop_audio(self):
        """Stop playback"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.update_status("PLAYBACK STOPPED", self.COLOR_DANGER)
        self.audio_status.config(text="● STOPPED", fg=self.COLOR_DANGER)

    def on_speed_change(self, value):
        """Handle speed change"""
        self.current_speed = float(value)
        self.speed_display.config(text=f"[ {self.current_speed:.1f}x ]")

        if self.is_playing and not self.is_paused:
            self.stop_audio()
            self.play_audio()

    def update_metrics(self):
        """Update technical metrics"""
        metadata = self.processor.get_metadata()
        if metadata:
            self.metric_labels['FORMAT'].config(text=metadata['format'])
            self.metric_labels['SAMPLE RATE'].config(text=f"{metadata['sample_rate']} Hz")
            self.metric_labels['CHANNELS'].config(text=str(metadata['channels']))
            self.metric_labels['BIT DEPTH'].config(text=f"{metadata['bit_depth']} bit")
            self.metric_labels['BITRATE'].config(text=f"{metadata['bitrate']:.0f} kbps")
            self.metric_labels['DURATION'].config(text=f"{metadata['duration']:.2f} sec")

    def draw_waveform(self):
        """Draw enhanced waveform visualization"""
        self.waveform_ax.clear()

        audio_data = self.processor.get_audio_data()
        if audio_data is None:
            self.style_axis(self.waveform_ax)
            self.waveform_ax.text(
                0.5, 0.5, '[ NO AUDIO DATA ]',
                ha='center', va='center',
                transform=self.waveform_ax.transAxes,
                color=self.COLOR_TEXT_DIM,
                fontsize=14
            )
            self.waveform_canvas.draw()
            return

        # Get samples
        if len(audio_data.shape) > 1:
            samples = audio_data[:, 0]
        else:
            samples = audio_data

        # Downsample for display
        display_samples = 3000
        if len(samples) > display_samples:
            step = len(samples) // display_samples
            samples = samples[::step]

        # Normalize
        samples = samples / (np.max(np.abs(samples)) + 1e-10)

        # Time axis in milliseconds
        duration_ms = self.processor.duration_ms
        time_ms = np.linspace(0, duration_ms, len(samples))

        # Plot waveform with gradient effect
        self.waveform_ax.plot(
            time_ms, samples,
            color=self.COLOR_ACCENT,
            linewidth=1.5,
            alpha=0.8
        )

        # Fill under the curve
        self.waveform_ax.fill_between(
            time_ms, samples, 0,
            color=self.COLOR_ACCENT,
            alpha=0.3
        )

        # Styling
        self.waveform_ax.set_xlim(0, duration_ms)
        self.waveform_ax.set_ylim(-1.1, 1.1)
        self.waveform_ax.set_xlabel('TIME (ms)', color=self.COLOR_ACCENT, fontsize=10, weight='bold')
        self.waveform_ax.set_ylabel('AMPLITUDE', color=self.COLOR_ACCENT, fontsize=10, weight='bold')
        self.waveform_ax.grid(True, alpha=0.2, color=self.COLOR_ACCENT, linestyle='--')
        self.style_axis(self.waveform_ax)

        # Add zero line
        self.waveform_ax.axhline(y=0, color=self.COLOR_CYAN, linewidth=1, alpha=0.5)

        self.waveform_canvas.draw()

    def draw_spectrum(self):
        """Draw enhanced spectrum visualization"""
        self.spectrum_ax.clear()

        audio_data = self.processor.get_audio_data()
        if audio_data is None:
            self.style_axis(self.spectrum_ax)
            self.spectrum_ax.text(
                0.5, 0.5, '[ NO AUDIO DATA ]',
                ha='center', va='center',
                transform=self.spectrum_ax.transAxes,
                color=self.COLOR_TEXT_DIM,
                fontsize=14
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

        # Positive frequencies only
        positive_freqs = freqs[:len(freqs)//2]
        magnitude = np.abs(fft[:len(fft)//2])

        # Convert to dB
        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        magnitude_db = magnitude_db - np.min(magnitude_db)

        # Smooth the spectrum
        from scipy import signal
        window_size = 51
        if len(magnitude_db) > window_size:
            magnitude_db = signal.savgol_filter(magnitude_db, window_size, 3)

        # Create bar chart with gradient colors
        num_bars = 80
        freq_bins = np.logspace(np.log10(20), np.log10(self.processor.sample_rate/2), num_bars + 1)

        bar_heights = []
        bar_colors = []

        for i in range(num_bars):
            freq_mask = (positive_freqs >= freq_bins[i]) & (positive_freqs < freq_bins[i+1])
            if np.any(freq_mask):
                height = np.mean(magnitude_db[freq_mask])
            else:
                height = 0

            bar_heights.append(height)

            # Color gradient: green -> cyan -> purple
            ratio = i / num_bars
            if ratio < 0.33:
                color = self.COLOR_ACCENT
            elif ratio < 0.66:
                color = self.COLOR_CYAN
            else:
                color = self.COLOR_PURPLE

            bar_colors.append(color)

        bar_centers = (freq_bins[:-1] + freq_bins[1:]) / 2
        bar_widths = freq_bins[1:] - freq_bins[:-1]

        self.spectrum_ax.bar(
            bar_centers, bar_heights,
            width=bar_widths,
            color=bar_colors,
            alpha=0.8,
            edgecolor=bar_colors,
            linewidth=0.5
        )

        # Styling
        self.spectrum_ax.set_xlim(20, self.processor.sample_rate/2)
        self.spectrum_ax.set_xlabel('FREQUENCY (Hz)', color=self.COLOR_ACCENT, fontsize=10, weight='bold')
        self.spectrum_ax.set_ylabel('MAGNITUDE (dB)', color=self.COLOR_ACCENT, fontsize=10, weight='bold')
        self.spectrum_ax.grid(True, alpha=0.2, color=self.COLOR_ACCENT, linestyle='--', which='both')
        self.spectrum_ax.set_xscale('log')
        self.style_axis(self.spectrum_ax)

        self.spectrum_canvas.draw()

    def run(self):
        """Run the application"""
        self.root.mainloop()

        # Cleanup
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
            except:
                pass


if __name__ == "__main__":
    app = EnhancedCyberpunkPlayer()
    app.run()
