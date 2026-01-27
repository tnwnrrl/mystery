"""
Audio Processing Module
Handles audio file loading, reversing, and format conversion
"""

import os
import sys
import tempfile
from pydub import AudioSegment
import numpy as np


def _setup_ffmpeg():
    """Set ffmpeg path for pydub (for bundled macOS app)"""
    # Check if running as bundled app (PyInstaller)
    if getattr(sys, 'frozen', False):
        bundle_dir = os.path.dirname(sys.executable)
        resources_dir = os.path.realpath(os.path.join(bundle_dir, '..', 'Resources'))
        frameworks_dir = os.path.realpath(os.path.join(bundle_dir, '..', 'Frameworks'))

        # Add bundle directories to PATH (pydub uses subprocess with PATH)
        current_path = os.environ.get("PATH", "")
        new_paths = [resources_dir, frameworks_dir, bundle_dir]
        for p in new_paths:
            if os.path.exists(p) and p not in current_path:
                os.environ["PATH"] = p + ":" + current_path
                current_path = os.environ["PATH"]

    # Also add ~/bin for development
    home_bin = os.path.expanduser("~/bin")
    if os.path.exists(home_bin) and home_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = home_bin + ":" + os.environ.get("PATH", "")


# Setup ffmpeg on module load
_setup_ffmpeg()


class AudioProcessor:
    def __init__(self):
        self.audio = None
        self.reversed_audio = None
        self.file_path = None
        self.sample_rate = None
        self.channels = None
        self.sample_width = None
        self.duration_ms = None
        self.bitrate = None

    def load_audio(self, file_path):
        """Load audio file (M4A, MP3, WAV)"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.m4a':
            self.audio = AudioSegment.from_file(file_path, format='m4a')
        elif file_ext == '.mp3':
            self.audio = AudioSegment.from_mp3(file_path)
        elif file_ext == '.wav':
            self.audio = AudioSegment.from_wav(file_path)
        else:
            raise ValueError("Unsupported file format. Only M4A, MP3, and WAV are supported.")

        self.file_path = file_path
        self.sample_rate = self.audio.frame_rate
        self.channels = self.audio.channels
        self.sample_width = self.audio.sample_width
        self.duration_ms = len(self.audio)
        self.bitrate = self.audio.frame_rate * self.audio.channels * self.audio.sample_width * 8

        return True

    def reverse_audio(self):
        """Reverse the loaded audio"""
        if self.audio is None:
            raise ValueError("No audio loaded. Please load an audio file first.")

        self.reversed_audio = self.audio.reverse()
        return self.reversed_audio

    def change_speed(self, speed_factor):
        """
        Change playback speed of reversed audio
        speed_factor: 0.5 = half speed, 1.0 = normal, 2.0 = double speed
        """
        if self.reversed_audio is None:
            raise ValueError("No reversed audio available. Please reverse audio first.")

        # Change frame rate to alter speed without changing pitch
        new_sample_rate = int(self.sample_rate * speed_factor)
        speed_changed = self.reversed_audio._spawn(
            self.reversed_audio.raw_data,
            overrides={'frame_rate': new_sample_rate}
        )
        # Convert back to original sample rate for consistent playback
        return speed_changed.set_frame_rate(self.sample_rate)

    def get_audio_data(self, audio_segment=None):
        """Get audio data as numpy array for visualization"""
        if audio_segment is None:
            audio_segment = self.reversed_audio if self.reversed_audio else self.audio

        if audio_segment is None:
            return None

        # Convert to numpy array
        samples = np.array(audio_segment.get_array_of_samples())

        # If stereo, reshape to (n_samples, 2)
        if self.channels == 2:
            samples = samples.reshape((-1, 2))

        return samples

    def export_reversed(self, output_path=None):
        """Export reversed audio to file"""
        if self.reversed_audio is None:
            raise ValueError("No reversed audio available. Please reverse audio first.")

        if output_path is None:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            output_path = temp_file.name
            temp_file.close()

        self.reversed_audio.export(output_path, format='wav')
        return output_path

    def get_metadata(self):
        """Get audio metadata for display"""
        if self.audio is None:
            return None

        return {
            'file_name': os.path.basename(self.file_path) if self.file_path else 'N/A',
            'duration': self.duration_ms / 1000.0,  # Convert to seconds
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'bit_depth': self.sample_width * 8,
            'bitrate': self.bitrate / 1000,  # Convert to kbps
            'format': os.path.splitext(self.file_path)[1].upper().replace('.', '') if self.file_path else 'N/A'
        }
