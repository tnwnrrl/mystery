"""
Visualization Module for Reserve Audio Analyzer
Matplotlib canvas and oscilloscope-style plotting utilities
"""

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib import patches
from scipy import signal

from config import Colors, DISPLAY_SAMPLES, WINDOW_SIZE_MS, FFT_SIZE, SAVGOL_WINDOW


class MplCanvas(FigureCanvasQTAgg):
    """Matplotlib canvas for PyQt5 with oscilloscope styling"""

    def __init__(self, parent=None, width=10, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=Colors.BLACK)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor(Colors.BLACK)
        super().__init__(self.fig)


def style_scope_axis(ax, xlabel, ylabel):
    """
    Style matplotlib axis with oscilloscope aesthetics

    Args:
        ax: matplotlib axes object
        xlabel: X-axis label text
        ylabel: Y-axis label text
    """
    # Hide spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Grid styling
    ax.grid(True, which='major', color=Colors.BORDER, linewidth=1.5, alpha=0.8)
    ax.grid(True, which='minor', color=Colors.BORDER, linewidth=0.5, alpha=0.4)
    ax.minorticks_on()

    # Tick and label styling
    ax.tick_params(colors=Colors.GREEN_MEDIUM, which='both', labelsize=9)
    ax.set_xlabel(xlabel, color=Colors.GREEN_MEDIUM, fontsize=10, weight='bold')
    ax.set_ylabel(ylabel, color=Colors.GREEN_MEDIUM, fontsize=10, weight='bold')

    # Border rectangle
    rect = patches.Rectangle(
        (0, 0), 1, 1,
        transform=ax.transAxes,
        fill=False,
        edgecolor=Colors.BORDER,
        linewidth=2
    )
    ax.add_patch(rect)


def prepare_waveform_samples(audio_data, channels):
    """
    Prepare audio samples for waveform display

    Args:
        audio_data: numpy array of audio samples
        channels: number of audio channels

    Returns:
        Normalized, downsampled samples ready for plotting
    """
    if audio_data is None:
        return None

    # Extract mono channel
    if len(audio_data.shape) > 1:
        samples = audio_data[:, 0]
    else:
        samples = audio_data

    # Downsample for display
    if len(samples) > DISPLAY_SAMPLES:
        step = len(samples) // DISPLAY_SAMPLES
        samples = samples[::step]

    # Normalize
    samples = samples / (np.max(np.abs(samples)) + 1e-10)

    return samples


def compute_spectrum(audio_data, sample_rate):
    """
    Compute frequency spectrum from audio data

    Args:
        audio_data: numpy array of audio samples
        sample_rate: audio sample rate in Hz

    Returns:
        tuple: (frequencies, magnitude_db)
    """
    if audio_data is None:
        return None, None

    # Extract mono channel
    if len(audio_data.shape) > 1:
        samples = audio_data[:, 0]
    else:
        samples = audio_data

    # FFT computation
    fft_size = min(FFT_SIZE, len(samples))
    chunk = samples[:fft_size]

    fft = np.fft.fft(chunk)
    freqs = np.fft.fftfreq(len(chunk), 1.0 / sample_rate)

    # Get positive frequencies only
    positive_freqs = freqs[:len(freqs)//2]
    magnitude = np.abs(fft[:len(fft)//2])

    # Convert to dB and normalize
    magnitude_db = 20 * np.log10(magnitude + 1e-10)
    magnitude_db = magnitude_db - np.min(magnitude_db)

    # Smooth with Savitzky-Golay filter
    if len(magnitude_db) > SAVGOL_WINDOW:
        magnitude_db = signal.savgol_filter(magnitude_db, SAVGOL_WINDOW, 3)

    return positive_freqs, magnitude_db


def draw_waveform_static(canvas, samples, duration_ms, playback_position=0, is_playing=False):
    """
    Draw static waveform on canvas

    Args:
        canvas: MplCanvas instance
        samples: prepared waveform samples (normalized, downsampled)
        duration_ms: total duration in milliseconds
        playback_position: current playback position in ms
        is_playing: whether audio is currently playing
    """
    ax = canvas.axes
    ax.clear()

    if samples is None:
        style_scope_axis(ax, 'TIME (ms)', 'AMPLITUDE (V)')
        ax.text(
            0.5, 0.5, 'NO SIGNAL',
            ha='center', va='center',
            transform=ax.transAxes,
            color=Colors.GREEN_MEDIUM, fontsize=18, weight='bold'
        )
        canvas.draw()
        return

    # Create time axis
    time_ms = np.linspace(0, duration_ms, len(samples))

    # Plot waveform
    ax.plot(time_ms, samples, color=Colors.GREEN_BRIGHT, linewidth=1.5, alpha=0.9)

    # Set limits
    ax.set_xlim(0, duration_ms)
    ax.set_ylim(-1.2, 1.2)
    style_scope_axis(ax, 'TIME (ms)', 'AMPLITUDE (V)')

    # Zero line
    ax.axhline(y=0, color=Colors.BORDER, linewidth=1.5, alpha=0.8)

    # Playback position marker
    if is_playing and playback_position > 0:
        ax.axvline(
            x=playback_position,
            color=Colors.YELLOW,
            linewidth=2,
            alpha=0.8,
            linestyle='--'
        )
        ax.text(
            playback_position, 1.1,
            f'{playback_position:.0f}ms',
            color=Colors.YELLOW,
            fontsize=9,
            ha='center',
            weight='bold'
        )

    canvas.draw()


def draw_spectrum_static(canvas, frequencies, magnitude_db, sample_rate):
    """
    Draw frequency spectrum on canvas

    Args:
        canvas: MplCanvas instance
        frequencies: frequency array
        magnitude_db: magnitude in dB
        sample_rate: audio sample rate in Hz
    """
    ax = canvas.axes
    ax.clear()

    if frequencies is None or magnitude_db is None:
        style_scope_axis(ax, 'FREQUENCY (Hz)', 'MAGNITUDE (dB)')
        ax.text(
            0.5, 0.5, 'NO SIGNAL',
            ha='center', va='center',
            transform=ax.transAxes,
            color=Colors.GREEN_MEDIUM, fontsize=18, weight='bold'
        )
        canvas.draw()
        return

    # Plot spectrum
    ax.plot(frequencies, magnitude_db, color=Colors.GREEN_BRIGHT, linewidth=1.5, alpha=0.9)
    ax.fill_between(frequencies, magnitude_db, 0, color=Colors.GREEN_BRIGHT, alpha=0.2)

    # Set limits and scale
    ax.set_xlim(20, sample_rate / 2)
    ax.set_xscale('log')
    style_scope_axis(ax, 'FREQUENCY (Hz)', 'MAGNITUDE (dB)')

    canvas.draw()


class WaveformAnimator:
    """
    Handles animated waveform display with blitting for performance
    """

    def __init__(self, canvas):
        self.canvas = canvas
        self._background = None
        self._line = None
        self._marker = None
        self._cached_samples = None

    def invalidate_cache(self):
        """Clear cached data (call when audio changes)"""
        self._background = None
        self._cached_samples = None

    def prepare_cache(self, audio_data):
        """
        Prepare cached data for animation

        Args:
            audio_data: numpy array of audio samples

        Returns:
            bool: True if cache prepared successfully
        """
        if audio_data is None:
            return False

        # Prepare and cache samples
        samples = prepare_waveform_samples(audio_data, 1)
        if samples is None:
            return False

        self._cached_samples = samples

        # Setup static background
        ax = self.canvas.axes
        ax.clear()
        ax.set_xlim(0, WINDOW_SIZE_MS)
        ax.set_ylim(-1.2, 1.2)
        style_scope_axis(ax, 'TIME (ms)', 'AMPLITUDE (V)')
        ax.axhline(y=0, color=Colors.BORDER, linewidth=1.5, alpha=0.8)

        # Create empty line for animation
        self._line, = ax.plot([], [], color=Colors.GREEN_BRIGHT, linewidth=1.5, alpha=0.9)
        self._marker = ax.axvline(
            x=WINDOW_SIZE_MS // 3,
            color=Colors.YELLOW,
            linewidth=2,
            alpha=0.5,
            linestyle='--'
        )

        # Draw and cache background
        self.canvas.draw()
        self._background = self.canvas.copy_from_bbox(ax.bbox)

        return True

    def update(self, playback_position, duration_ms):
        """
        Update animation frame using blitting

        Args:
            playback_position: current playback position in ms
            duration_ms: total duration in ms
        """
        # Initialize cache if needed
        if self._background is None or self._cached_samples is None:
            return

        ax = self.canvas.axes
        total_points = len(self._cached_samples)
        window_size_points = int((WINDOW_SIZE_MS / duration_ms) * total_points)

        # Calculate window position
        start_point = int((playback_position / duration_ms) * total_points)
        if start_point >= total_points:
            start_point = 0
        end_point = min(start_point + window_size_points, total_points)

        # Get window samples
        window_samples = self._cached_samples[start_point:end_point]
        if len(window_samples) == 0:
            window_samples = self._cached_samples[:window_size_points]

        time_window = np.linspace(0, WINDOW_SIZE_MS, len(window_samples))

        # Restore background and update line (blitting)
        self.canvas.restore_region(self._background)
        self._line.set_data(time_window, window_samples)
        ax.draw_artist(self._line)
        ax.draw_artist(self._marker)
        self.canvas.blit(ax.bbox)
