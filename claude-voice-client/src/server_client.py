"""HTTP client for communicating with the STT server."""

import requests
import time
from typing import Optional


class ServerClient:
    """Client for communicating with the transcription server."""

    def __init__(self, server_url: str):
        """Initialize the client.

        Args:
            server_url: URL of the transcription server (e.g., http://10.0.0.205:8000)
        """
        self.server_url = server_url.rstrip('/')

    def health(self) -> dict:
        """Check server health.

        Returns:
            Dictionary with server status, or error info if failed
        """
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Cannot connect to server"}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Connection timeout"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def transcribe(self, audio_wav: bytes, language: str = None) -> dict:
        """Send audio for transcription.

        Args:
            audio_wav: WAV audio data (16kHz, mono, PCM16)
            language: Optional language code

        Returns:
            Dictionary with transcription results

        Raises:
            requests.HTTPError: If the request fails
        """
        files = {'audio': ('audio.wav', audio_wav, 'audio/wav')}
        data = {}
        if language:
            data['language'] = language

        response = requests.post(
            f"{self.server_url}/transcribe",
            files=files,
            data=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
