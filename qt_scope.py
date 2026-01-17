"""
Reverse Audio Player - PyQt5 Oscilloscope Edition
Professional measurement equipment aesthetic with full styling control
"""

import sys
import os
import numpy as np
import threading
import pygame
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QSlider, QFileDialog,
                             QFrame, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib import patches
from audio_processor import AudioProcessor


class MplCanvas(FigureCanvasQTAgg):
    """Matplotlib canvas for PyQt5"""
    def __init__(self, parent=None, width=10, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#000000')
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('#000000')
        super(MplCanvas, self).__init__(self.fig)


class OscilloscopeApp(QMainWindow):
    """Professional Oscilloscope-style Audio Analyzer"""

    def __init__(self):
        super().__init__()

        # Audio processor
        self.processor = AudioProcessor()

        # Playback state
        pygame.mixer.init()
        self.is_playing = False
        self.is_paused = False
        self.current_speed = 1.0
        self.temp_audio_file = None
        self.playback_start_time = 0
        self.playback_position = 0

        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.setInterval(50)  # Update every 50ms

        self.init_ui()
        self.apply_stylesheet()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle('AUDIO SPECTRUM ANALYZER ASA-2000')
        self.setGeometry(100, 100, 1600, 950)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header
        self.create_header(main_layout)

        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # Left panel
        self.create_control_panel(content_layout)

        # Right panel
        self.create_display_panel(content_layout)

        main_layout.addLayout(content_layout, stretch=1)

        # Status bar
        self.create_status_bar(main_layout)

    def create_header(self, layout):
        """Create header"""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)

        title = QLabel('AUDIO SPECTRUM ANALYZER')
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 36, QFont.Bold))
        header_layout.addWidget(title)

        subtitle = QLabel('MODEL: ASA-2000  |  REVERSE AUDIO ANALYSIS SYSTEM')
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont('Courier New', 12))
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

    def create_control_panel(self, layout):
        """Create control panel"""
        panel = QFrame()
        panel.setObjectName("controlPanel")
        panel.setFixedWidth(420)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(10)

        # File input
        file_section = self.create_section("FILE INPUT")
        file_layout = QVBoxLayout()
        file_layout.setContentsMargins(10, 35, 10, 10)

        self.file_label = QLabel('NO SIGNAL')
        self.file_label.setObjectName("fileLabel")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setFont(QFont('Courier New', 13, QFont.Bold))
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)

        load_btn = QPushButton('LOAD FILE')
        load_btn.setObjectName("loadButton")
        load_btn.setFont(QFont('Courier New', 14, QFont.Bold))
        load_btn.setFixedHeight(45)
        load_btn.clicked.connect(self.load_file)
        file_layout.addWidget(load_btn)

        file_section.setLayout(file_layout)
        panel_layout.addWidget(file_section)

        # Signal processor
        proc_section = self.create_section("SIGNAL PROCESSOR")
        proc_layout = QVBoxLayout()
        proc_layout.setContentsMargins(10, 35, 10, 10)

        reverse_btn = QPushButton('⟲ REVERSE SIGNAL')
        reverse_btn.setObjectName("reverseButton")
        reverse_btn.setFont(QFont('Courier New', 14, QFont.Bold))
        reverse_btn.setFixedHeight(45)
        reverse_btn.clicked.connect(self.reverse_audio)
        proc_layout.addWidget(reverse_btn)

        self.reverse_status = QLabel('⚫ STANDBY')
        self.reverse_status.setObjectName("reverseStatus")
        self.reverse_status.setAlignment(Qt.AlignCenter)
        self.reverse_status.setFont(QFont('Courier New', 13, QFont.Bold))
        proc_layout.addWidget(self.reverse_status)

        proc_section.setLayout(proc_layout)
        panel_layout.addWidget(proc_section)

        # Signal parameters
        params_section = self.create_section("SIGNAL PARAMETERS")
        params_container = QVBoxLayout()
        params_container.setContentsMargins(10, 35, 10, 10)
        params_layout = QGridLayout()
        params_layout.setSpacing(8)

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

            param_widget = QFrame()
            param_widget.setObjectName("parameterBox")
            param_layout = QVBoxLayout(param_widget)
            param_layout.setContentsMargins(5, 5, 5, 5)

            label = QLabel(name)
            label.setObjectName("paramLabel")
            label.setFont(QFont('Courier New', 10))
            param_layout.addWidget(label)

            value = QLabel(f"{default} {unit}")
            value.setObjectName("paramValue")
            value.setFont(QFont('Courier New', 16, QFont.Bold))
            param_layout.addWidget(value)

            self.param_labels[name] = (value, unit)
            params_layout.addWidget(param_widget, row, col)

        params_container.addLayout(params_layout)
        params_section.setLayout(params_container)
        panel_layout.addWidget(params_section)

        # Playback
        play_section = self.create_section("PLAYBACK CONTROL")
        play_container = QVBoxLayout()
        play_container.setContentsMargins(10, 35, 10, 10)
        play_layout = QGridLayout()
        play_layout.setSpacing(5)

        self.play_btn = QPushButton('▶ PLAY')
        self.play_btn.setObjectName("playButton")
        self.play_btn.setFont(QFont('Courier New', 13, QFont.Bold))
        self.play_btn.setFixedHeight(40)
        self.play_btn.clicked.connect(self.play_audio)
        play_layout.addWidget(self.play_btn, 0, 0)

        self.pause_btn = QPushButton('❚❚ PAUSE')
        self.pause_btn.setObjectName("playButton")
        self.pause_btn.setFont(QFont('Courier New', 13, QFont.Bold))
        self.pause_btn.setFixedHeight(40)
        self.pause_btn.clicked.connect(self.pause_audio)
        play_layout.addWidget(self.pause_btn, 0, 1)

        self.stop_btn = QPushButton('■ STOP')
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setFont(QFont('Courier New', 13, QFont.Bold))
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.clicked.connect(self.stop_audio)
        play_layout.addWidget(self.stop_btn, 1, 0, 1, 2)

        play_container.addLayout(play_layout)
        play_section.setLayout(play_container)
        panel_layout.addWidget(play_section)

        # Timebase
        time_section = self.create_section("TIMEBASE CONTROL")
        time_layout = QVBoxLayout()
        time_layout.setContentsMargins(10, 35, 10, 10)

        speed_display = QFrame()
        speed_display.setObjectName("speedDisplay")
        speed_display.setFixedHeight(70)
        speed_layout = QVBoxLayout(speed_display)

        self.speed_label = QLabel('1.00x')
        self.speed_label.setObjectName("speedValue")
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.speed_label.setFont(QFont('Courier New', 28, QFont.Bold))
        speed_layout.addWidget(self.speed_label)
        time_layout.addWidget(speed_display)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setObjectName("speedSlider")
        self.speed_slider.setMinimum(5)
        self.speed_slider.setMaximum(20)
        self.speed_slider.setValue(10)
        self.speed_slider.setFixedHeight(30)
        self.speed_slider.valueChanged.connect(self.on_speed_change)
        time_layout.addWidget(self.speed_slider)

        markers = QHBoxLayout()
        for speed in ['0.5x', '1.0x', '1.5x', '2.0x']:
            marker = QLabel(speed)
            marker.setObjectName("speedMarker")
            marker.setFont(QFont('Courier New', 9))
            marker.setAlignment(Qt.AlignCenter)
            markers.addWidget(marker)
        time_layout.addLayout(markers)

        time_section.setLayout(time_layout)
        panel_layout.addWidget(time_section)

        panel_layout.addStretch()
        layout.addWidget(panel)

    def create_display_panel(self, layout):
        """Create display panel with oscilloscope"""
        panel = QFrame()
        panel.setObjectName("displayPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(10)

        # CH1 - Waveform
        ch1_label = QLabel('CH1: TIME DOMAIN WAVEFORM')
        ch1_label.setObjectName("channelLabel")
        ch1_label.setAlignment(Qt.AlignCenter)
        ch1_label.setFont(QFont('Courier New', 14, QFont.Bold))
        panel_layout.addWidget(ch1_label)

        self.waveform_canvas = MplCanvas(self, width=12, height=3.8)
        self.style_scope_axis(self.waveform_canvas.axes, 'TIME (ms)', 'AMPLITUDE (V)')
        panel_layout.addWidget(self.waveform_canvas)

        # CH2 - Spectrum
        ch2_label = QLabel('CH2: FREQUENCY DOMAIN SPECTRUM')
        ch2_label.setObjectName("channelLabel")
        ch2_label.setAlignment(Qt.AlignCenter)
        ch2_label.setFont(QFont('Courier New', 14, QFont.Bold))
        panel_layout.addWidget(ch2_label)

        self.spectrum_canvas = MplCanvas(self, width=12, height=3.8)
        self.style_scope_axis(self.spectrum_canvas.axes, 'FREQUENCY (Hz)', 'MAGNITUDE (dB)')
        panel_layout.addWidget(self.spectrum_canvas)

        layout.addWidget(panel, stretch=1)

    def create_status_bar(self, layout):
        """Create status bar"""
        status = QFrame()
        status.setObjectName("statusBar")
        status.setFixedHeight(40)
        status_layout = QHBoxLayout(status)

        self.status_label = QLabel('⚫ SYSTEM READY')
        self.status_label.setObjectName("statusLabel")
        self.status_label.setFont(QFont('Courier New', 12, QFont.Bold))
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.time_label = QLabel('00:00.000')
        self.time_label.setObjectName("timeLabel")
        self.time_label.setFont(QFont('Courier New', 12, QFont.Bold))
        status_layout.addWidget(self.time_label)

        layout.addWidget(status)

    def create_section(self, title):
        """Create section frame"""
        section = QFrame()
        section.setObjectName("section")

        label = QLabel(f"═══ {title} ═══")
        label.setObjectName("sectionTitle")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont('Courier New', 12, QFont.Bold))
        label.setParent(section)
        label.setGeometry(0, 0, 400, 30)

        return section

    def style_scope_axis(self, ax, xlabel, ylabel):
        """Style matplotlib axis"""
        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.grid(True, which='major', color='#001a00', linewidth=1.5, alpha=0.8)
        ax.grid(True, which='minor', color='#001a00', linewidth=0.5, alpha=0.4)
        ax.minorticks_on()

        ax.tick_params(colors='#00aa00', which='both', labelsize=9)
        ax.set_xlabel(xlabel, color='#00aa00', fontsize=10, weight='bold')
        ax.set_ylabel(ylabel, color='#00aa00', fontsize=10, weight='bold')

        rect = patches.Rectangle(
            (0, 0), 1, 1,
            transform=ax.transAxes,
            fill=False,
            edgecolor='#001a00',
            linewidth=2
        )
        ax.add_patch(rect)

    def apply_stylesheet(self):
        """Apply QSS stylesheet"""
        stylesheet = """
        QMainWindow {
            background-color: #000000;
        }

        #header {
            background-color: #000000;
            border: 2px solid #001a00;
        }

        #title {
            color: #00ff41;
        }

        #subtitle {
            color: #00aa00;
        }

        #controlPanel {
            background-color: #0a0a0a;
            border: 2px solid #001a00;
        }

        #displayPanel {
            background-color: #000000;
            border: 2px solid #001a00;
        }

        #section {
            background-color: #0a0a0a;
            border: 2px solid #001a00;
            border-radius: 5px;
        }

        #sectionTitle {
            color: #00ff41;
        }

        #fileLabel, #reverseStatus {
            color: #00aa00;
        }

        QPushButton {
            background-color: #003300;
            color: #00ff41;
            border: 2px solid #00ff41;
            border-radius: 5px;
            padding: 8px;
        }

        QPushButton:hover {
            background-color: #00ff41;
            color: #000000;
        }

        #reverseButton {
            border-color: #ffff00;
            color: #ffff00;
        }

        #reverseButton:hover {
            background-color: #ffff00;
        }

        #stopButton {
            border-color: #ff0000;
            color: #ff0000;
        }

        #stopButton:hover {
            background-color: #ff0000;
        }

        #parameterBox {
            background-color: #000000;
            border: 2px solid #001a00;
            border-radius: 3px;
        }

        #paramLabel {
            color: #00aa00;
        }

        #paramValue {
            color: #00ff41;
        }

        #speedDisplay {
            background-color: #000000;
            border: 3px solid #001a00;
            border-radius: 5px;
        }

        #speedValue {
            color: #00ff41;
        }

        #speedMarker {
            color: #00aa00;
        }

        QSlider::groove:horizontal {
            background: #001a00;
            height: 8px;
            border-radius: 4px;
        }

        QSlider::handle:horizontal {
            background: #00ff41;
            width: 20px;
            margin: -6px 0;
            border-radius: 10px;
        }

        QSlider::add-page:horizontal {
            background: #001a00;
        }

        QSlider::sub-page:horizontal {
            background: #00ff41;
        }

        #channelLabel {
            color: #00ff41;
        }

        #statusBar {
            background-color: #0a0a0a;
            border: 2px solid #001a00;
        }

        #statusLabel, #timeLabel {
            color: #00ff41;
        }
        """
        self.setStyleSheet(stylesheet)

    def update_status(self, message, color='#00ff41'):
        """Update status"""
        self.status_label.setText(f'● {message}')
        self.status_label.setStyleSheet(f'color: {color};')

    def load_file(self):
        """Load file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "SELECT AUDIO FILE",
            "",
            "Audio Files (*.mp3 *.wav);;MP3 Files (*.mp3);;WAV Files (*.wav)"
        )

        if file_path:
            try:
                self.update_status("LOADING SIGNAL...", '#ffff00')
                self.processor.load_audio(file_path)

                filename = os.path.basename(file_path)
                self.file_label.setText(filename)
                self.file_label.setStyleSheet('color: #00ff41;')
                self.update_status("SIGNAL ACQUIRED")

                self.update_parameters()
                self.draw_waveform()
                self.draw_spectrum()

            except Exception as e:
                self.update_status(f"ERROR: {str(e)}", '#ff0000')
                self.file_label.setText("LOAD FAILED")
                self.file_label.setStyleSheet('color: #ff0000;')

    def reverse_audio(self):
        """Reverse audio"""
        if self.processor.audio is None:
            self.update_status("ERROR: NO SIGNAL", '#ff0000')
            return

        try:
            self.update_status("PROCESSING...", '#ffff00')
            self.reverse_status.setText('⚫ PROCESSING')
            self.reverse_status.setStyleSheet('color: #ffff00;')

            def reverse_thread():
                self.processor.reverse_audio()
                QTimer.singleShot(0, self.on_reverse_complete)

            thread = threading.Thread(target=reverse_thread, daemon=True)
            thread.start()

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", '#ff0000')
            self.reverse_status.setText('⚫ FAILED')
            self.reverse_status.setStyleSheet('color: #ff0000;')

    def on_reverse_complete(self):
        """Reverse complete"""
        self.reverse_status.setText('● REVERSED')
        self.reverse_status.setStyleSheet('color: #00ff41;')
        self.update_status("SIGNAL REVERSED")
        self.draw_waveform()
        self.draw_spectrum()

    def play_audio(self):
        """Play audio"""
        if self.processor.reversed_audio is None:
            self.update_status("ERROR: NO REVERSED SIGNAL", '#ff0000')
            return

        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.update_status("PLAYBACK ACTIVE")
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
                self.playback_start_time = pygame.time.get_ticks()
                self.playback_position = 0
                self.animation_timer.start()
                self.update_status(f"PLAYING @ {self.current_speed:.2f}x")

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", '#ff0000')

    def pause_audio(self):
        """Pause"""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.animation_timer.stop()
            self.update_status("PAUSED", '#ffff00')

    def stop_audio(self):
        """Stop"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.animation_timer.stop()
        self.playback_position = 0
        self.draw_waveform()
        self.draw_spectrum()
        self.update_status("STOPPED", '#ff0000')

    def on_speed_change(self, value):
        """Speed change"""
        self.current_speed = value / 10.0
        self.speed_label.setText(f'{self.current_speed:.2f}x')

        if self.is_playing and not self.is_paused:
            self.stop_audio()
            self.play_audio()

    def update_animation(self):
        """Update animation during playback"""
        if not self.is_playing or self.is_paused:
            return

        # Check if still playing
        if not pygame.mixer.music.get_busy():
            self.stop_audio()
            return

        # Just increment position for visual effect
        duration_ms = self.processor.duration_ms if self.processor.duration_ms else 1000
        self.playback_position += 50  # Move by 50ms each update

        if self.playback_position >= duration_ms:
            self.playback_position = 0  # Loop back

        # Update time display
        current_time = self.playback_position / 1000.0
        total_time = duration_ms / 1000.0
        self.time_label.setText(f"{current_time:05.2f} / {total_time:05.2f}")

        # Redraw waveform with moving window effect
        self.draw_waveform_animated()

    def update_parameters(self):
        """Update parameters"""
        metadata = self.processor.get_metadata()
        if metadata:
            self.param_labels['Fs'][0].setText(f"{metadata['sample_rate']} {self.param_labels['Fs'][1]}")
            self.param_labels['CH'][0].setText(f"{metadata['channels']} {self.param_labels['CH'][1]}")
            self.param_labels['BITS'][0].setText(f"{metadata['bit_depth']} {self.param_labels['BITS'][1]}")
            self.param_labels['RATE'][0].setText(f"{metadata['bitrate']:.0f} {self.param_labels['RATE'][1]}")
            self.param_labels['TIME'][0].setText(f"{metadata['duration']:.2f} {self.param_labels['TIME'][1]}")
            self.param_labels['FMT'][0].setText(f"{metadata['format']} {self.param_labels['FMT'][1]}")

    def draw_waveform(self):
        """Draw waveform"""
        self.waveform_canvas.axes.clear()

        audio_data = self.processor.get_audio_data()
        if audio_data is None:
            self.style_scope_axis(self.waveform_canvas.axes, 'TIME (ms)', 'AMPLITUDE (V)')
            self.waveform_canvas.axes.text(
                0.5, 0.5, 'NO SIGNAL',
                ha='center', va='center',
                transform=self.waveform_canvas.axes.transAxes,
                color='#00aa00', fontsize=18, weight='bold'
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
        self.waveform_canvas.axes.plot(time_ms, samples, color='#00ff41', linewidth=4, alpha=0.3)
        self.waveform_canvas.axes.plot(time_ms, samples, color='#00ff41', linewidth=2, alpha=0.6)
        self.waveform_canvas.axes.plot(time_ms, samples, color='#00ff41', linewidth=1, alpha=1.0)

        self.waveform_canvas.axes.set_xlim(0, duration_ms)
        self.waveform_canvas.axes.set_ylim(-1.2, 1.2)
        self.style_scope_axis(self.waveform_canvas.axes, 'TIME (ms)', 'AMPLITUDE (V)')

        self.waveform_canvas.axes.axhline(y=0, color='#001a00', linewidth=1.5, alpha=0.8)

        # Add playback position marker
        if self.is_playing and self.playback_position > 0:
            self.waveform_canvas.axes.axvline(
                x=self.playback_position,
                color='#ffff00',
                linewidth=2,
                alpha=0.8,
                linestyle='--'
            )
            # Add position label
            self.waveform_canvas.axes.text(
                self.playback_position,
                1.1,
                f'{self.playback_position:.0f}ms',
                color='#ffff00',
                fontsize=9,
                ha='center',
                weight='bold'
            )

        self.waveform_canvas.draw()

    def draw_waveform_animated(self):
        """Draw waveform with scrolling animation effect"""
        self.waveform_canvas.axes.clear()

        audio_data = self.processor.get_audio_data()
        if audio_data is None:
            self.style_scope_axis(self.waveform_canvas.axes, 'TIME (ms)', 'AMPLITUDE (V)')
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

        duration_ms = self.processor.duration_ms
        total_points = len(samples)

        # Create scrolling window effect
        # Show a moving window of the waveform
        window_size_ms = 2000  # Show 2 seconds at a time
        window_size_points = int((window_size_ms / duration_ms) * total_points)

        # Calculate which part to show based on playback position
        start_point = int((self.playback_position / duration_ms) * total_points)
        end_point = min(start_point + window_size_points, total_points)

        if start_point >= total_points:
            start_point = 0
            end_point = window_size_points

        # Get window samples
        window_samples = samples[start_point:end_point]
        if len(window_samples) == 0:
            window_samples = samples[:window_size_points]

        # Create time axis for window
        time_window = np.linspace(0, window_size_ms, len(window_samples))

        # Draw with glow effect - scrolling from left to right
        self.waveform_canvas.axes.plot(time_window, window_samples, color='#00ff41', linewidth=4, alpha=0.3)
        self.waveform_canvas.axes.plot(time_window, window_samples, color='#00ff41', linewidth=2, alpha=0.6)
        self.waveform_canvas.axes.plot(time_window, window_samples, color='#00ff41', linewidth=1, alpha=1.0)

        self.waveform_canvas.axes.set_xlim(0, window_size_ms)
        self.waveform_canvas.axes.set_ylim(-1.2, 1.2)
        self.style_scope_axis(self.waveform_canvas.axes, 'TIME (ms)', 'AMPLITUDE (V)')

        self.waveform_canvas.axes.axhline(y=0, color='#001a00', linewidth=1.5, alpha=0.8)

        # Add vertical position marker at a fixed position (like oscilloscope trigger)
        marker_pos = window_size_ms * 0.3  # Show at 30% from left
        self.waveform_canvas.axes.axvline(
            x=marker_pos,
            color='#ffff00',
            linewidth=2,
            alpha=0.5,
            linestyle='--'
        )

        self.waveform_canvas.draw()

    def draw_spectrum(self):
        """Draw spectrum"""
        self.spectrum_canvas.axes.clear()

        audio_data = self.processor.get_audio_data()
        if audio_data is None:
            self.style_scope_axis(self.spectrum_canvas.axes, 'FREQUENCY (Hz)', 'MAGNITUDE (dB)')
            self.spectrum_canvas.axes.text(
                0.5, 0.5, 'NO SIGNAL',
                ha='center', va='center',
                transform=self.spectrum_canvas.axes.transAxes,
                color='#00aa00', fontsize=18, weight='bold'
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
        self.spectrum_canvas.axes.plot(positive_freqs, magnitude_db, color='#00ff41', linewidth=4, alpha=0.3)
        self.spectrum_canvas.axes.plot(positive_freqs, magnitude_db, color='#00ff41', linewidth=2, alpha=0.6)
        self.spectrum_canvas.axes.plot(positive_freqs, magnitude_db, color='#00ff41', linewidth=1, alpha=1.0)

        self.spectrum_canvas.axes.fill_between(positive_freqs, magnitude_db, 0, color='#00ff41', alpha=0.2)

        self.spectrum_canvas.axes.set_xlim(20, self.processor.sample_rate/2)
        self.spectrum_canvas.axes.set_xscale('log')
        self.style_scope_axis(self.spectrum_canvas.axes, 'FREQUENCY (Hz)', 'MAGNITUDE (dB)')

        self.spectrum_canvas.draw()

    def closeEvent(self, event):
        """Cleanup on close"""
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
            except:
                pass
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OscilloscopeApp()
    window.show()
    sys.exit(app.exec_())
