"""Audio recording using PyAudio."""

import pyaudio
import wave
import io
from pathlib import Path
from typing import Optional, List


class AudioRecorder:
    """Record audio from microphone."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_size: int = 1024):
        """Initialize the audio recorder.

        Args:
            sample_rate: Sample rate in Hz (16000 for Whisper)
            channels: Number of audio channels (1 for mono)
            chunk_size: Number of frames per buffer
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.recording = False
        self.frames: List[bytes] = []

    def list_devices(self) -> List[dict]:
        """List available audio input devices.

        Returns:
            List of device info dictionaries
        """
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels']
                })
        return devices

    def start_recording(self, device_index: int = None):
        """Start recording audio.

        Args:
            device_index: Device index to use, or None for default

        Raises:
            Exception: If recording fails to start
        """
        if device_index is None:
            device_index = self.audio.get_default_input_device_info()['index']

        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size
        )
        self.frames = []
        self.recording = True

    def record_chunk(self):
        """Record a single chunk of audio.

        Call this repeatedly while recording to capture audio.
        """
        if self.recording and self.stream and self.stream.is_active():
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                # Silently handle overflow errors
                pass

    def stop_recording(self) -> bytes:
        """Stop recording and return WAV bytes.

        Returns:
            WAV audio data as bytes

        Raises:
            Exception: If no recording is in progress
        """
        self.recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        # Convert to WAV in memory
        output = io.BytesIO()
        with wave.open(output, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))

        output.seek(0)
        return output.read()

    def cleanup(self):
        """Cleanup audio resources."""
        self.recording = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        self.audio.terminate()
