"""
Reverse Audio Player - PyQt5 Oscilloscope Edition
Professional measurement equipment aesthetic with full styling control
"""

import sys
import os
import tempfile
import threading
import pygame
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QFrame, QGridLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from config import (
    Colors, Fonts, Layout, get_stylesheet,
    DISPLAY_SAMPLES, WINDOW_SIZE_MS,
    ANIMATION_INTERVAL_MS, PLAYBACK_STEP_MS,
    FFT_SIZE, SAVGOL_WINDOW
)
from visualization import (
    MplCanvas, style_scope_axis,
    prepare_waveform_samples, compute_spectrum,
    draw_waveform_static, draw_spectrum_static,
    WaveformAnimator
)
from audio_processor import AudioProcessor


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
        self.temp_audio_file = None
        self.playback_start_time = 0
        self.playback_position = 0

        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.setInterval(ANIMATION_INTERVAL_MS)

        # Waveform animator (initialized after UI)
        self.waveform_animator = None

        self.init_ui()
        self.apply_stylesheet()

        # Initialize waveform animator after canvas is created
        self.waveform_animator = WaveformAnimator(self.waveform_canvas)

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle('AUDIO SPECTRUM ANALYZER ASA-2000')
        self.setGeometry(Layout.WINDOW_X, Layout.WINDOW_Y, Layout.WINDOW_WIDTH, Layout.WINDOW_HEIGHT)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(Layout.MAIN_MARGIN, Layout.MAIN_MARGIN, Layout.MAIN_MARGIN, Layout.MAIN_MARGIN)
        main_layout.setSpacing(Layout.MAIN_SPACING)

        # Header
        self.create_header(main_layout)

        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(Layout.MAIN_SPACING)

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
        header.setFixedHeight(Layout.HEADER_HEIGHT)
        header_layout = QVBoxLayout(header)

        title = QLabel('AUDIO SPECTRUM ANALYZER')
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 34, QFont.Bold))
        header_layout.addWidget(title)

        subtitle = QLabel('MODEL: ASA-2000  |  REVERSE AUDIO ANALYSIS SYSTEM')
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont('Courier New', 14))
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

    def create_control_panel(self, layout):
        """Create control panel"""
        panel = QFrame()
        panel.setObjectName("controlPanel")
        panel.setFixedWidth(Layout.CONTROL_PANEL_WIDTH)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(10)

        # File input
        file_section = self.create_section("FILE INPUT")
        file_layout = QVBoxLayout()
        file_layout.setContentsMargins(10, 37, 10, 10)

        self.file_label = QLabel('NO SIGNAL')
        self.file_label.setObjectName("fileLabel")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setFont(QFont('Courier New', 15, QFont.Bold))
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)

        load_btn = QPushButton('LOAD FILE')
        load_btn.setObjectName("loadButton")
        load_btn.setFont(QFont('Courier New', 17, QFont.Bold))
        load_btn.setFixedHeight(Layout.BUTTON_HEIGHT)
        load_btn.clicked.connect(self.load_file)
        file_layout.addWidget(load_btn)

        file_section.setLayout(file_layout)
        panel_layout.addWidget(file_section)

        # Signal processor
        proc_section = self.create_section("SIGNAL PROCESSOR")
        proc_layout = QVBoxLayout()
        proc_layout.setContentsMargins(10, 37, 10, 10)

        reverse_btn = QPushButton('⟲ REVERSE SIGNAL')
        reverse_btn.setObjectName("reverseButton")
        reverse_btn.setFont(QFont('Courier New', 17, QFont.Bold))
        reverse_btn.setFixedHeight(Layout.BUTTON_HEIGHT)
        reverse_btn.clicked.connect(self.reverse_audio)
        proc_layout.addWidget(reverse_btn)

        self.reverse_status = QLabel('⚫ STANDBY')
        self.reverse_status.setObjectName("reverseStatus")
        self.reverse_status.setAlignment(Qt.AlignCenter)
        self.reverse_status.setFont(QFont('Courier New', 15, QFont.Bold))
        proc_layout.addWidget(self.reverse_status)

        proc_section.setLayout(proc_layout)
        panel_layout.addWidget(proc_section)

        # Signal parameters
        params_section = self.create_section("SIGNAL PARAMETERS")
        params_container = QVBoxLayout()
        params_container.setContentsMargins(10, 37, 10, 10)
        params_layout = QGridLayout()
        params_layout.setSpacing(14)

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
            param_layout.setContentsMargins(9, 9, 9, 9)

            label = QLabel(name)
            label.setObjectName("paramLabel")
            label.setFont(QFont('Courier New', 14))
            param_layout.addWidget(label)

            value = QLabel(f"{default} {unit}")
            value.setObjectName("paramValue")
            value.setFont(QFont('Courier New', 20, QFont.Bold))
            param_layout.addWidget(value)

            self.param_labels[name] = (value, unit)
            params_layout.addWidget(param_widget, row, col)

        params_container.addLayout(params_layout)
        params_section.setLayout(params_container)
        panel_layout.addWidget(params_section)

        # Playback
        play_section = self.create_section("PLAYBACK CONTROL")
        play_container = QVBoxLayout()
        play_container.setContentsMargins(10, 37, 10, 10)
        play_layout = QGridLayout()
        play_layout.setSpacing(9)

        self.play_btn = QPushButton('▶ PLAY')
        self.play_btn.setObjectName("playButton")
        self.play_btn.setFont(QFont('Courier New', 15, QFont.Bold))
        self.play_btn.setFixedHeight(Layout.BUTTON_HEIGHT_SMALL)
        self.play_btn.clicked.connect(self.play_audio)
        play_layout.addWidget(self.play_btn, 0, 0)

        self.pause_btn = QPushButton('❚❚ PAUSE')
        self.pause_btn.setObjectName("playButton")
        self.pause_btn.setFont(QFont('Courier New', 15, QFont.Bold))
        self.pause_btn.setFixedHeight(Layout.BUTTON_HEIGHT_SMALL)
        self.pause_btn.clicked.connect(self.pause_audio)
        play_layout.addWidget(self.pause_btn, 0, 1)

        self.stop_btn = QPushButton('■ STOP')
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setFont(QFont('Courier New', 15, QFont.Bold))
        self.stop_btn.setFixedHeight(Layout.BUTTON_HEIGHT_SMALL)
        self.stop_btn.clicked.connect(self.stop_audio)
        play_layout.addWidget(self.stop_btn, 1, 0, 1, 2)

        play_container.addLayout(play_layout)
        play_section.setLayout(play_container)
        panel_layout.addWidget(play_section)

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
        ch1_label.setFont(QFont('Courier New', 17, QFont.Bold))
        panel_layout.addWidget(ch1_label)

        self.waveform_canvas = MplCanvas(self, width=Layout.CANVAS_WIDTH, height=Layout.CANVAS_HEIGHT)
        style_scope_axis(self.waveform_canvas.axes, 'TIME (ms)', 'AMPLITUDE (V)')
        panel_layout.addWidget(self.waveform_canvas)

        # CH2 - Spectrum
        ch2_label = QLabel('CH2: FREQUENCY DOMAIN SPECTRUM')
        ch2_label.setObjectName("channelLabel")
        ch2_label.setAlignment(Qt.AlignCenter)
        ch2_label.setFont(QFont('Courier New', 17, QFont.Bold))
        panel_layout.addWidget(ch2_label)

        self.spectrum_canvas = MplCanvas(self, width=Layout.CANVAS_WIDTH, height=Layout.CANVAS_HEIGHT)
        style_scope_axis(self.spectrum_canvas.axes, 'FREQUENCY (Hz)', 'MAGNITUDE (dB)')
        panel_layout.addWidget(self.spectrum_canvas)

        layout.addWidget(panel, stretch=1)

    def create_status_bar(self, layout):
        """Create status bar"""
        status = QFrame()
        status.setObjectName("statusBar")
        status.setFixedHeight(Layout.STATUS_BAR_HEIGHT)
        status_layout = QHBoxLayout(status)

        self.status_label = QLabel('⚫ SYSTEM READY')
        self.status_label.setObjectName("statusLabel")
        self.status_label.setFont(QFont('Courier New', 15, QFont.Bold))
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.time_label = QLabel('00:00.000')
        self.time_label.setObjectName("timeLabel")
        self.time_label.setFont(QFont('Courier New', 17, QFont.Bold))
        status_layout.addWidget(self.time_label)

        layout.addWidget(status)

    def create_section(self, title):
        """Create section frame"""
        section = QFrame()
        section.setObjectName("section")

        label = QLabel(f"═══ {title} ═══")
        label.setObjectName("sectionTitle")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont('Courier New', 17, QFont.Bold))
        label.setParent(section)
        label.setGeometry(0, 0, Layout.SECTION_TITLE_WIDTH, Layout.SECTION_TITLE_HEIGHT)

        return section

    def apply_stylesheet(self):
        """Apply QSS stylesheet from config"""
        self.setStyleSheet(get_stylesheet())

    def update_status(self, message, color=None):
        """Update status"""
        if color is None:
            color = Colors.GREEN_BRIGHT
        self.status_label.setText(f'● {message}')
        self.status_label.setStyleSheet(f'color: {color};')

    def load_file(self):
        """Load file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "SELECT AUDIO FILE",
            "",
            "Audio Files (*.m4a *.mp3 *.wav);;M4A Files (*.m4a);;MP3 Files (*.mp3);;WAV Files (*.wav)"
        )

        if file_path:
            try:
                self.update_status("LOADING SIGNAL...", Colors.YELLOW)
                self.processor.load_audio(file_path)

                filename = os.path.basename(file_path)
                self.file_label.setText(filename)
                self.file_label.setStyleSheet(f'color: {Colors.GREEN_BRIGHT};')
                self.update_status("SIGNAL ACQUIRED")

                self.update_parameters()
                self.draw_waveform()
                self.draw_spectrum()

            except FileNotFoundError:
                self.update_status("ERROR: FILE NOT FOUND", Colors.RED)
                self.file_label.setText("FILE NOT FOUND")
                self.file_label.setStyleSheet(f'color: {Colors.RED};')
            except Exception as e:
                error_msg = str(e)
                # ffmpeg 관련 에러 체크
                if 'ffmpeg' in error_msg.lower() or 'ffprobe' in error_msg.lower():
                    self.update_status("ERROR: FFMPEG NOT FOUND", Colors.RED)
                    self.file_label.setText("INSTALL FFMPEG")
                elif 'codec' in error_msg.lower() or 'decode' in error_msg.lower():
                    self.update_status("ERROR: UNSUPPORTED CODEC", Colors.RED)
                    self.file_label.setText("CODEC ERROR")
                else:
                    self.update_status(f"ERROR: {error_msg[:30]}", Colors.RED)
                    self.file_label.setText("LOAD FAILED")
                self.file_label.setStyleSheet(f'color: {Colors.RED};')

    def reverse_audio(self):
        """Reverse audio"""
        if self.processor.audio is None:
            self.update_status("ERROR: NO SIGNAL", Colors.RED)
            return

        try:
            self.update_status("PROCESSING...", Colors.YELLOW)
            self.reverse_status.setText('⚫ PROCESSING')
            self.reverse_status.setStyleSheet(f'color: {Colors.YELLOW};')

            def reverse_thread():
                self.processor.reverse_audio()
                QTimer.singleShot(0, self.on_reverse_complete)

            thread = threading.Thread(target=reverse_thread, daemon=True)
            thread.start()

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", Colors.RED)
            self.reverse_status.setText('⚫ FAILED')
            self.reverse_status.setStyleSheet(f'color: {Colors.RED};')

    def on_reverse_complete(self):
        """Reverse complete"""
        self.reverse_status.setText('● REVERSED')
        self.reverse_status.setStyleSheet(f'color: {Colors.GREEN_BRIGHT};')
        self.update_status("SIGNAL REVERSED")
        # Invalidate animation cache (audio data changed)
        self.waveform_animator.invalidate_cache()
        self.draw_waveform()
        self.draw_spectrum()

    def play_audio(self):
        """Play audio"""
        if self.processor.reversed_audio is None:
            self.update_status("ERROR: NO REVERSED SIGNAL", Colors.RED)
            return

        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.update_status("PLAYBACK ACTIVE")
            else:
                audio_to_play = self.processor.change_speed(1.0)

                if self.temp_audio_file:
                    try:
                        os.remove(self.temp_audio_file)
                    except OSError:
                        pass  # File already deleted or in use

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
                self.update_status("PLAYING")

        except Exception as e:
            self.update_status(f"ERROR: {str(e)}", Colors.RED)

    def pause_audio(self):
        """Pause"""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.animation_timer.stop()
            self.update_status("PAUSED", Colors.YELLOW)

    def stop_audio(self):
        """Stop"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.animation_timer.stop()
        self.playback_position = 0
        # Invalidate animation cache
        self.waveform_animator.invalidate_cache()
        self.draw_waveform()
        self.draw_spectrum()
        self.update_status("STOPPED", Colors.RED)

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
        self.playback_position += PLAYBACK_STEP_MS

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
        """Draw waveform using visualization module"""
        audio_data = self.processor.get_audio_data()
        samples = prepare_waveform_samples(audio_data, self.processor.channels)
        draw_waveform_static(
            self.waveform_canvas,
            samples,
            self.processor.duration_ms,
            self.playback_position,
            self.is_playing
        )

    def draw_waveform_animated(self):
        """Draw waveform with blitting using WaveformAnimator"""
        # Initialize animator cache if needed
        if self.waveform_animator._background is None:
            audio_data = self.processor.get_audio_data()
            if not self.waveform_animator.prepare_cache(audio_data):
                return

        # Update animation frame
        self.waveform_animator.update(
            self.playback_position,
            self.processor.duration_ms
        )

    def draw_spectrum(self):
        """Draw spectrum using visualization module"""
        audio_data = self.processor.get_audio_data()
        frequencies, magnitude_db = compute_spectrum(audio_data, self.processor.sample_rate)
        draw_spectrum_static(
            self.spectrum_canvas,
            frequencies,
            magnitude_db,
            self.processor.sample_rate
        )

    def closeEvent(self, event):
        """Cleanup on close"""
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
            except OSError:
                pass  # File in use or permission denied
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OscilloscopeApp()
    window.show()
    sys.exit(app.exec_())
