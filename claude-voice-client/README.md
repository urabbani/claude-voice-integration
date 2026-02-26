# Claude Voice Client

Voice input for Claude Code — dictate prompts and commands instead of typing.

## Architecture

```
┌─────────────────┐         ┌──────────────────────┐         ┌──────────────────┐
│   WSL Client    │         │   RTX 5090 Server    │         │   Claude Code    │
├─────────────────┤         ├──────────────────────┤         ├──────────────────┤
│ • Hotkey listen │         │ • faster-whisper     │         │ • Receives text  │
│ • Audio capture │ ──────▶ │ • CUDA GPU accel     │ ──────▶ │ • Processes      │
│ • Send audio    │  HTTP   │ • /transcribe API    │  Text   │ • Displays resp  │
│ • Copy to clip  │         │                      │         │                  │
└─────────────────┘         └──────────────────────┘         └──────────────────┘
```

## Quick Start

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install portaudio19-dev python3-pip python3-venv
```

### 2. Setup Virtual Environment

```bash
cd ~/claude-voice-client
python3 -m venv venv
source venv/bin/activate
pip install pyaudio pynput requests pyyaml colorama
```

### 3. Configure (optional)

Edit `config.yaml` if needed:

```yaml
hotkey: "ctrl+shift+v"
server_url: "http://YOUR_SERVER_IP:8000"
```

### 4. Run

```bash
python src/main.py
```

### 5. Use

1. Press `Ctrl+Shift+V` to start recording
2. Speak your prompt
3. Press `Ctrl+Shift+V` again to stop
4. Text appears and is copied to clipboard
5. Paste into Claude Code

## Usage with Claude Code

The transcribed text is automatically copied to your clipboard using `wl-copy`.
After recording, simply paste in Claude Code with `Ctrl+Shift+V` (if your
terminal supports it) or use your terminal's paste function.

## Commands

```bash
# Run client
python src/main.py

# Test audio devices
python src/main.py --test-audio

# Use custom config
python src/main.py --config /path/to/config.yaml
```

## Troubleshooting

### No audio devices found

```bash
# Check PulseAudio
pactl info

# List microphones
pacmd list-sources

# Restart PulseAudio
pulseaudio --kill
pulseaudio --start
```

### Server unreachable

```bash
# Ping server
ping YOUR_SERVER_IP

# Check server status
curl http://YOUR_SERVER_IP:8000/health

# On server machine, start server:
# systemctl --user start claude-voice-server
```

### Hotkey not working

- Try a different hotkey in `config.yaml`
- Check for conflicts with other applications
- Make sure you're not in a terminal that captures the hotkey

### Recording too short/long

Edit `config.yaml`:

```yaml
audio:
  max_duration: 30  # seconds
```

### WSL2 Audio Issues

If WSL2 audio isn't working:

```bash
# Install PulseAudio on Windows side
# Download from: https://www.freedesktop.org/wiki/Software/PulseAudio/Ports/Windows/Support/

# Or use WSLg (built into Windows 11)
wsl --update
```

## Configuration

Full `config.yaml` options:

```yaml
hotkey: "ctrl+shift+v"           # Global hotkey to toggle recording
server_url: "http://YOUR_SERVER_IP:8000"  # STT server URL
audio:
  sample_rate: 16000              # Audio sample rate (Whisper optimal)
  channels: 1                     # Mono audio
  chunk_size: 1024                # Audio buffer size
  max_duration: 30                # Max recording length (seconds)
recording:
  indicator: "🎤"                 # Recording indicator emoji
  processing: "⏳"                # Processing indicator
  success: "✅"                   # Success indicator
  error: "❌"                     # Error indicator
retry:
  max_attempts: 3                 # Retry attempts for server errors
  backoff: 1.0                    # Initial backoff (seconds)
```

## Auto-Start

To start the client automatically when you open a terminal, add to `~/.bashrc`:

```bash
# Claude Voice Client
if [ -f ~/claude-voice-client/venv/bin/activate ]; then
    source ~/claude-voice-client/venv/bin/activate
    python ~/claude-voice-client/src/main.py &
fi
```
