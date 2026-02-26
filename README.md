# 🎤 Claude Voice Integration

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-WSL%2FLinux-lightgrey.svg)](https://github.com/urabbani/claude-voice-integration)

Voice input integration for Claude Code — dictate prompts and commands instead of typing. Features GPU-accelerated transcription using faster-whisper with CUDA support.

## ✨ Features

- 🎤 **High-Quality Transcription** — Uses OpenAI Whisper (medium model) with GPU acceleration
- ⚡ **Fast Response** — ~1 second transcription time with RTX 5090
- 🔊 **Auto-Paste Support** — Optional named pipe for direct terminal injection
- 🔄 **Client-Server Architecture** — Separate transcription server for optimal resource usage
- 📦 **Easy Setup** — Automated installation scripts for both client and server
- 🎛️ **Configurable** — Custom hotkeys, audio settings, and model options

## 🏗️ Architecture

```
┌─────────────────────┐         ┌──────────────────────────┐         ┌──────────────────┐
│   Client Machine    │         │   Server Machine (GPU)   │         │   Claude Code    │
│   (WSL/Linux)       │         │   (WSL/Linux + NVIDIA)   │         │                  │
├─────────────────────┤         ├──────────────────────────┤         ├──────────────────┤
│ • Sounddevice I/O   │ ──────▶ │ • faster-whisper        │ ──────▶ │ • Receives text  │
│ • WAV Encoding      │  HTTP   │ • CUDA Acceleration     │  Text   │ • Processes      │
│ • Auto-paste pipe   │         │ • Medium Model (769MB)   │         │ • Displays resp  │
│ • Clipboard support │         │ • FastAPI Server        │         │                  │
└─────────────────────┘         └──────────────────────────┘         └──────────────────┘
```

## 📋 Requirements

### Client Machine
- Python 3.9 or higher
- Linux/WSL with PulseAudio support
- Microphone accessible from the system
- `wl-clipboard` for clipboard support (optional)

### Server Machine
- NVIDIA GPU with CUDA support (tested on RTX 5090)
- Python 3.9 or higher
- 5GB+ VRAM for medium model
- Ubuntu/Debian-based Linux

### Optional Dependencies
```bash
# Client
sudo apt install portaudio19-dev python3-pip python3-venv wl-clipboard

# Server
sudo apt install nvidia-cuda-toolkit libcublas12
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/urabbani/claude-voice-integration.git
cd claude-voice-integration
```

### 2. Server Setup (GPU Machine)

```bash
cd claude-voice-server
./setup.sh
./install-service.sh  # For auto-start on boot
```

The server will download the Whisper model (~769MB) on first run.

### 3. Client Setup

```bash
cd claude-voice-client
./setup.sh
```

### 4. Configure

Edit `claude-voice-client/config.yaml`:

```yaml
server_url: "http://YOUR_SERVER_IP:8000"
```

### 5. Run

```bash
voice-record
```

1. Speak your prompt
2. Press Enter
3. Text is transcribed and copied to clipboard
4. Paste into Claude Code with `Ctrl+Shift+V`

## 📖 Usage

### Basic Voice Recording

```bash
voice-record
```

```
🎤 Recording... (press Enter to stop)

⏳ Transcribing...
✅ "Hello world, how can you help me today?"

📋 Copied to clipboard (paste with Ctrl+Shift+V)
```

### Auto-Paste to Claude Code Terminal

In your Claude Code terminal, run:

```bash
~/claude-voice-client/voice-pipe.sh
```

Then use `voice-record` in another terminal — text will automatically appear in your Claude Code terminal!

### Service Management

**Server:**
```bash
systemctl --user start claude-voice-server    # Start
systemctl --user stop claude-voice-server     # Stop
systemctl --user status claude-voice-server   # Status
journalctl --user -u claude-voice-server -f   # Logs
```

## ⚙️ Configuration

### Client Config (`config.yaml`)

```yaml
hotkey: "ctrl+shift+v"           # Global hotkey (reserved for future)
server_url: "http://YOUR_SERVER_IP:8000"
audio:
  sample_rate: 16000              # Whisper optimal
  channels: 1                     # Mono
  chunk_size: 1024
  max_duration: 30                # Max recording (seconds)
recording:
  indicator: "🎤"
  processing: "⏳"
  success: "✅"
  error: "❌"
retry:
  max_attempts: 3
  backoff: 1.0
```

### Server Config (`config.yaml`)

```yaml
host: "0.0.0.0"
port: 8000
model:
  name: "medium"                  # tiny, base, small, medium, large-v3
  device: "cuda"
  compute_type: "float16"         # RTX 5090 optimized
transcription:
  beam_size: 5
  vad_filter: true                # Voice activity detection
  word_timestamps: false
```

### Model Performance

| Model | Size | VRAM | Latency | Accuracy |
|-------|------|------|---------|----------|
| tiny | 39MB | 1GB | ~200ms | Fair |
| base | 74MB | 1GB | ~300ms | Good |
| small | 244MB | 2GB | ~500ms | Very Good |
| **medium** | **769MB** | **5GB** | **~1s** | **Excellent** |
| large-v3 | 3.1GB | 10GB | ~2s | Best |

## 🔧 Troubleshooting

### Server: `libcublas.so.12 not found`

```bash
sudo apt install libcublas12
systemctl --user restart claude-voice-server
```

### Client: No audio devices found

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
# Test connection
curl http://YOUR_SERVER_IP:8000/health

# Check firewall
sudo ufw allow 8000/tcp
```

### Clipboard not working

```bash
sudo apt install wl-clipboard
```

## 📁 Project Structure

```
claude-voice-integration/
├── claude-voice-client/          # Voice recording client
│   ├── src/
│   │   ├── audio_recorder.py     # Sounddevice-based recording
│   │   ├── server_client.py      # HTTP client for STT
│   │   ├── ui.py                 # Terminal UI
│   │   └── voice-record.py       # Main recording script
│   ├── voice-pipe.sh             # Auto-paste helper
│   ├── config.yaml               # Client configuration
│   └── setup.sh                  # Installation script
│
└── claude-voice-server/          # STT transcription server
    ├── src/
    │   ├── server.py             # FastAPI application
    │   ├── transcriber.py        # faster-whisper wrapper
    │   └── models.py             # Pydantic schemas
    ├── models/                   # Whisper model storage
    ├── config.yaml               # Server configuration
    └── setup.sh                  # Installation script
```

## 🌐 API Reference

### POST /transcribe

Transcribe audio to text.

**Request:**
```bash
curl -X POST http://YOUR_SERVER_IP:8000/transcribe \
  -F "audio=@recording.wav" \
  -F "language=en"
```

**Response:**
```json
{
  "text": "transcribed text here",
  "duration": 3.2,
  "language": "en",
  "processing_time": 0.45
}
```

### GET /health

Check server status.

**Response:**
```json
{
  "status": "healthy",
  "model": "medium",
  "device": "cuda"
}
```

## 🚧 Development

### Running in Development Mode

**Server:**
```bash
cd claude-voice-server
source venv/bin/activate
python -m uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
```

**Client:**
```bash
cd claude-voice-client
source venv/bin/activate
python src/voice-record.py
```

### Running Tests

```bash
# Test audio devices
python -m src.main --test-audio

# Test server health
curl http://localhost:8000/health
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [faster-whisper](https://github.com/guillaumekln/faster-whisper) — Fast Whisper inference
- [OpenAI Whisper](https://github.com/openai/whisper) — Original Whisper model
- [sounddevice](https://python-sounddevice.readthedocs.io/) — Audio I/O
- [FastAPI](https://fastapi.tiangolo.com/) — Python web framework

## 📧 Support

For issues, questions, or suggestions, please [open an issue](https://github.com/urabbani/claude-voice-integration/issues/new).

---

Made with ❤️ for the Claude Code community
