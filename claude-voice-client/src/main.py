#!/usr/bin/env python3
"""
Claude Voice Client - Voice input for Claude Code

This client captures audio from your microphone, sends it to a transcription
server, and displays the text. The text is also copied to your clipboard
for easy pasting into Claude Code.
"""

import sys
import yaml
import time
import signal
import threading
from pathlib import Path
from typing import Optional
from colorama import Fore, Style

from .audio_recorder import AudioRecorder
from .server_client import ServerClient
from .hotkey_manager import HotkeyManager
from .ui import UI


class VoiceClient:
    """Main voice client application."""

    def __init__(self, config_path: str = None):
        """Initialize the voice client.

        Args:
            config_path: Optional path to configuration file
        """
        # Load config
        config_file = Path(config_path or Path(__file__).parent.parent / "config.yaml")
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)

        self.ui = UI(self.config)
        self.server = ServerClient(self.config['server_url'])
        self.recorder = AudioRecorder(
            sample_rate=self.config['audio']['sample_rate'],
            channels=self.config['audio']['channels'],
            chunk_size=self.config['audio']['chunk_size']
        )
        self.hotkey_mgr = HotkeyManager(self.config['hotkey'])

        self.recording = False
        self.start_time: Optional[float] = None
        self.update_thread: Optional[threading.Thread] = None
        self.running = True

    def check_server(self) -> bool:
        """Check if server is reachable.

        Returns:
            True if server is healthy, False otherwise
        """
        self.ui.print_info("Checking server connection...")
        health = self.server.health()

        if health.get('status') == 'healthy':
            self.ui.print_success(
                f"Server connected: {health.get('model')} model on {health.get('device')}"
            )
            return True
        else:
            self.ui.print_error(f"Server unreachable at {self.config['server_url']}")
            self.ui.print_info("Make sure the server is running on 10.0.0.205")
            self.ui.print_info("On the server: systemctl --user start claude-voice-server")
            return False

    def toggle_recording(self):
        """Toggle recording state (called by hotkey)."""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording audio."""
        if self.recording:
            return  # Already recording

        try:
            self.recording = True
            self.start_time = time.time()
            self.recorder.start_recording()

            # Start UI update thread
            self.update_thread = threading.Thread(target=self._update_recording_ui, daemon=True)
            self.update_thread.start()

        except Exception as e:
            self.recording = False
            self.ui.print_error(f"Failed to start recording: {e}")

    def _update_recording_ui(self):
        """Update recording UI in background thread."""
        while self.recording and self.running:
            duration = time.time() - self.start_time if self.start_time else 0

            # Record chunk
            self.recorder.record_chunk()

            # Update UI
            self.ui.print_recording(duration)

            # Check timeout
            if duration > self.config['audio']['max_duration']:
                self.ui.print_info(f"\nMaximum duration ({self.config['audio']['max_duration']}s) reached")
                self.stop_recording()
                break

            time.sleep(0.05)  # ~20 FPS

    def stop_recording(self):
        """Stop recording and transcribe."""
        if not self.recording:
            return  # Not recording

        self.recording = False
        duration = time.time() - self.start_time if self.start_time else 0

        try:
            # Get audio and cleanup recorder
            audio_wav = self.recorder.stop_recording()

            if duration < 0.5:
                self.ui.clear_line()
                self.ui.print_warning("Recording too short, ignoring")
                return

            # Transcribe
            self.ui.print_processing()
            result = self._transcribe_with_retry(audio_wav)

            if result and result.get('text'):
                text = result['text']
                self.ui.clear_line()
                self.ui.print_success(text)
                self._copy_to_clipboard(text)
            else:
                self.ui.clear_line()
                self.ui.print_warning("No speech detected")

        except Exception as e:
            self.ui.clear_line()
            self.ui.print_error(str(e))

    def _transcribe_with_retry(self, audio_wav: bytes) -> Optional[dict]:
        """Transcribe with retry logic.

        Args:
            audio_wav: WAV audio data

        Returns:
            Transcription result dict, or None if all retries fail
        """
        max_attempts = self.config['retry']['max_attempts']
        backoff = self.config['retry']['backoff']

        for attempt in range(max_attempts):
            try:
                return self.server.transcribe(audio_wav)
            except Exception as e:
                if attempt < max_attempts - 1:
                    time.sleep(backoff * (2 ** attempt))
                else:
                    raise

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard.

        Args:
            text: Text to copy
        """
        try:
            import subprocess
            subprocess.run(
                ['wl-copy'],
                input=text.encode(),
                check=True,
                stderr=subprocess.DEVNULL
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass  # wl-copy not available, silently fail

    def run(self):
        """Run the voice client."""
        # Print banner
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Claude Voice Client{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

        # Check server first
        if not self.check_server():
            return

        # List audio devices
        devices = self.recorder.list_devices()
        if not devices:
            self.ui.print_error("No audio input devices found")
            return

        self.ui.print_devices(devices)
        self.ui.print_info(f"Press {self.config['hotkey']} to start/stop recording")
        self.ui.print_info("Press Ctrl+C to quit\n")

        # Setup signal handler
        signal.signal(signal.SIGINT, self._signal_handler)

        # Start hotkey listener
        self.hotkey_mgr.start(self.toggle_recording)

        # Keep running
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.ui.print_info("\nShutting down...")
        self.running = False
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """Cleanup resources."""
        self.recording = False
        self.hotkey_mgr.stop()
        self.recorder.cleanup()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Voice Client - Voice input for Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main              # Run with default config
  python -m src.main -t           # Test audio devices
  python -m src.main -c custom.yaml  # Use custom config
        """
    )

    parser.add_argument(
        '--config', '-c',
        help='Path to config.yaml'
    )
    parser.add_argument(
        '--test-audio', '-t',
        action='store_true',
        help='Test audio devices and exit'
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Claude Voice Client 1.0.0'
    )

    args = parser.parse_args()

    client = VoiceClient(args.config)

    if args.test_audio:
        devices = client.recorder.list_devices()
        client.ui.print_devices(devices)
        client.recorder.cleanup()
        return

    try:
        client.run()
    except Exception as e:
        client.ui.print_error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
