#!/bin/bash
# Voice input pipe for Claude Code
# Run this in your Claude Code terminal

PIPE="/tmp/claude-voice-pipe"

# Create the pipe if it doesn't exist
if [ ! -p "$PIPE" ]; then
    mkfifo "$PIPE"
fi

echo "🎤 Voice pipe ready. Commands from 'voice-record' will appear here."
echo "Press Ctrl+C to stop"
echo ""

# Read from pipe and execute each line
while true; do
    if read -r line < "$PIPE"; then
        # Clear the line and add the voice text
        tput el
        echo "$line"
    fi
done
