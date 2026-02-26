#!/bin/bash
# Auto-paste daemon for voice integration
# This monitors for voice input and auto-pastes to active terminal
# Usage: voice-auto-paste-daemon &

PIPE="/tmp/claude-voice-inject"
ACTIVE_TERMINAL=""

# Detect active terminal using focus
detect_active_terminal() {
    # Try to find the most recently focused terminal
    if command -v xdotool &> /dev/null; then
        WINDOW_ID=$(xdotool getactivewindow)
        WINDOW_NAME=$(xdotool getwindowname "$WINDOW_ID")
        echo "$WINDOW_NAME"
    elif command -v tmux &> /dev/null && [ -n "$TMUX" ]; then
        tmux display-message -p '#S'
    else
        echo "terminal"
    fi
}

# Create injection pipe
mkfifo "$PIPE" 2>/dev/null || true

echo "🎤 Voice Auto-Paste Daemon Running"
echo "Listening for voice input..."
echo ""
echo "Voice input will auto-paste to your active terminal."
echo "Press Ctrl+C to stop"
echo ""

# Monitor pipe for voice input
while true; do
    if read -r text < "$PIPE"; then
        # Clear current line and inject text
        tput el
        echo "$text"

        # Beep to indicate paste (optional)
        echo -en "\a" > /dev/tty$(detect_active_terminal)
    fi
done
