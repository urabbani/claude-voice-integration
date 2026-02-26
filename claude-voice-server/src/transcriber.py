"""Whisper transcriber using faster-whisper with CUDA acceleration."""

import time
import yaml
import tempfile
import wave
import numpy as np
from faster_whisper import WhisperModel
from pathlib import Path
from typing import Optional


class Transcriber:
    """Handles audio transcription using faster-whisper."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the transcriber with configuration.

        Args:
            config_path: Path to the configuration file
        """
        config_file = Path(__file__).parent.parent / config_path
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)

        model_config = self.config['model']
        print(f"Loading Whisper model: {model_config['name']}...")
        print(f"Device: {model_config['device']}, Compute: {model_config['compute_type']}")

        self.model = WhisperModel(
            model_size_or_path=model_config['name'],
            device=model_config['device'],
            compute_type=model_config['compute_type'],
            download_root=str(Path(__file__).parent.parent / "models")
        )
        print(f"Model loaded successfully on {model_config['device']}")

    def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> dict:
        """Transcribe audio bytes to text.

        Args:
            audio_bytes: WAV audio data (16kHz, mono, PCM16)
            language: Language code (e.g., 'en'), or None for auto-detect

        Returns:
            Dictionary with text, duration, language, and processing_time
        """
        start_time = time.time()

        # Save to temp file and use the file path
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(audio_bytes)

        try:
            segments, info = self.model.transcribe(
                temp_path,
                beam_size=self.config['transcription']['beam_size'],
                vad_filter=self.config['transcription']['vad_filter'],
                language=language,
                word_timestamps=self.config['transcription']['word_timestamps']
            )

            text = ''.join(segment.text for segment in segments)
            processing_time = time.time() - start_time

            return {
                "text": text.strip(),
                "duration": info.duration,
                "language": info.language if info.language else "unknown",
                "processing_time": processing_time
            }
        finally:
            # Clean up temp file
            import os
            try:
                os.unlink(temp_path)
            except:
                pass
