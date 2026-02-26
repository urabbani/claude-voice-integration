#!/usr/bin/env python3
"""
Auto-paste daemon for voice integration
Runs in background and injects transcribed text into the terminal
"""

import sys
import os
import time
import signal
import threading
from pathlib import Path

VOICE_PIPE = "/tmp/claude-voice-inject"


def inject_to_terminal(text: str):
    """Inject text into the terminal as if it was typed."""
    # Try different methods for terminal injection

    # Method 1: Direct write to stdout (works in same terminal)
    try:
        # Clear line and print
        sys.stdout.write("\r\033[K")  # Clear line
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
        return True
    except:
        pass

    # Method 2: Try to write to specific terminal
    try:
        import tty
        with open("/dev/tty", "w") as f:
            f.write("\r\033[K")  # Clear line
            f.write(text + "\n")
            f.flush()
        return True
    except:
        pass

    return False


def main():
    # Create pipe if it doesn't exist
    try:
        os.mkfifo(VOICE_PIPE)
    except FileExistsError:
        pass

    print("🎤 Voice Auto-Paste Daemon")
    print("=" * 40)
    print("Voice input will automatically appear here")
    print("Press Ctrl+C to stop")
    print("")

    running = True

    def signal_handler(signum, frame):
        nonlocal running
        print("\n🛑 Stopping daemon...")
        running = False
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Monitor pipe for input
    while running:
        try:
            with open(VOICE_PIPE, 'r') as pipe:
                # Set non-blocking
                import fcntl
                flags = fcntl.fcntl(pipe.fileno(), fcntl.F_GETFL)
                fcntl.fcntl(pipe.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)

                while running:
                    try:
                        line = pipe.readline()
                        if line:
                            text = line.strip()
                            if text:
                                # Inject the text
                                inject_to_terminal(text)
                    except IOError:
                        # No data available
                        time.sleep(0.05)
        except FileNotFoundError:
            time.sleep(1)


if __name__ == "__main__":
    main()
