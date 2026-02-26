#!/usr/bin/env python3
"""
Voice recording script - run with: voice-record
"""

import sys
import os
import time
import yaml
from pathlib import Path

# Add src to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / "src"))

from audio_recorder import AudioRecorder
from server_client import ServerClient

# Pipe for auto-paste to Claude Code
VOICE_PIPE = "/tmp/claude-voice-pipe"


def main():
    print("🎤 Recording... (press Enter to stop)")
    print()

    # Initialize recorder
    recorder = AudioRecorder()

    try:
        recorder.start_recording()
    except Exception as e:
        print(f"❌ Failed to start recording: {e}")
        print("\nTroubleshooting:")
        print("  - Check microphone: pactl list sources")
        print("  - Check PulseAudio: pulseaudio --check -v")
        sys.exit(1)

    # Start recording in background
    import threading

    recording = True
    frames = []

    def record_audio():
        nonlocal frames
        while recording:
            recorder.record_chunk()
            time.sleep(0.05)

    thread = threading.Thread(target=record_audio, daemon=True)
    thread.start()

    # Wait for Enter
    input()

    # Stop recording
    recording = False
    thread.join(timeout=1)

    print()
    print("⏳ Transcribing...")

    try:
        audio = recorder.stop_recording()
    except Exception as e:
        print(f"❌ Failed to stop recording: {e}")
        sys.exit(1)

    # Check if we got any audio
    if len(audio) < 1000:
        print("❌ Recording too short - no audio captured")
        sys.exit(1)

    # Transcribe
    try:
        config_path = SCRIPT_DIR / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        client = ServerClient(config['server_url'])
        result = client.transcribe(audio)

        text = result.get('text', '').strip()

        if text:
            print(f'✅ "{text}"')

            # Copy to clipboard
            try:
                import subprocess
                subprocess.run(
                    ['wl-copy'],
                    input=text.encode(),
                    check=True,
                    stderr=subprocess.DEVNULL
                )
                print()
                print("📋 Copied to clipboard (paste with Ctrl+Shift+V)")
            except:
                print()
                print("(Clipboard not available)")

            # Write to pipe for auto-paste
            try:
                with open(VOICE_PIPE, 'w') as pipe:
                    pipe.write(text + '\n')
                print(f"🎤 Sent to voice pipe (auto-paste in Claude Code terminal)")
            except:
                pass  # Pipe not open, that's ok
        else:
            print("❌ No speech detected")

    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
