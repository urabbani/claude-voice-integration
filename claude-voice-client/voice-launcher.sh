#!/bin/bash
# Voice integration launcher
# Start auto-paste daemon when terminal opens

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPE="/tmp/claude-voice-inject"
PIDFILE="$HOME/.voice-auto-paste.pid"

# Check if daemon is already running
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        # Daemon is running, just update pipe
        export VOICE_INJECT_PIPE="$PIPE"
        echo "✅ Voice auto-paste daemon already running (PID: $PID)"
    else
        # Stale PID file, start daemon
        rm -f "$PIDFILE"
        "$SCRIPT_DIR/voice-auto-paste.py" &
        echo $! > "$PIDFILE"
        export VOICE_INJECT_PIPE="$PIPE"
        echo "🎤 Voice auto-paste daemon started"
    fi
else
    # Start daemon in background
    "$SCRIPT_DIR/voice-auto-paste.py" &
    echo $! > "$PIDFILE"
    export VOICE_INJECT_PIPE="$PIPE"
    echo "🎤 Voice auto-paste daemon started"
fi

echo "💬 Voice input will auto-paste to this terminal"
