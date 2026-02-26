# Claude Voice STT Server

Fast Whisper transcription server using RTX 5090 GPU acceleration.

## Architecture

```
Client Request ──────▶ FastAPI Server ──────▶ faster-whisper (CUDA)
                          │                        │
                     /transcribe             RTX 5090 GPU
                          │                        │
                     JSON Response ◀───────────────┘
```

## Quick Start

### 1. Verify CUDA

```bash
nvidia-smi  # Should show RTX 5090
```

### 2. Install Python Dependencies

```bash
cd ~/claude-voice-server
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn[standard] faster-whisper pyyaml python-multipart
```

### 3. Configure (optional)

Edit `config.yaml` to change model or settings:

```yaml
model:
  name: "medium"  # Options: tiny, base, small, medium, large-v3
  device: "cuda"
  compute_type: "float16"
```

### 4. Run Server

```bash
python -m uvicorn src.server:app --host 0.0.0.0 --port 8000
```

The server will download the Whisper model on first run (~1.5GB for medium).

## Auto-Start (systemd)

Create a user service to auto-start the server on boot:

```bash
# Create service directory
mkdir -p ~/.config/systemd/user

# Create service file
cat > ~/.config/systemd/user/claude-voice-server.service << 'EOF'
[Unit]
Description=Claude Voice STT Server
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/claude-voice-server
ExecStart=%h/claude-voice-server/venv/bin/python -m uvicorn src.server:app --host 0.0.0.0 --port 8000
Restart=always
Environment=PATH=%h/claude-voice-server/venv/bin:/usr/bin

[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user daemon-reload
systemctl --user enable claude-voice-server
systemctl --user start claude-voice-server

# Check status
systemctl --user status claude-voice-server
```

## API

### POST /transcribe

Transcribe audio file to text.

**Request:**
```
POST /transcribe
Content-Type: multipart/form-data

audio: <WAV file, 16kHz, mono, PCM16>
language: "en" (optional, auto-detect if omitted)
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

**Example:**
```bash
# Test with curl
curl -X POST http://localhost:8000/transcribe \
  -F "audio=@test.wav" \
  -F "language=en"
```

### GET /health

Check server status and model information.

**Response:**
```json
{
  "status": "healthy",
  "model": "medium",
  "device": "cuda"
}
```

## Performance

With RTX 5090 GPU:

| Model | Download Size | VRAM Usage | Speed | Accuracy |
|-------|---------------|------------|-------|----------|
| tiny | 39MB | ~1GB | ~0.2s | Fair |
| base | 74MB | ~1GB | ~0.3s | Good |
| small | 244MB | ~2GB | ~0.5s | Very Good |
| medium | 769MB | ~5GB | ~1s | Excellent |
| large-v3 | 3.1GB | ~10GB | ~2s | Best |

**Recommendation:** Use `medium` for best balance of speed and accuracy.

## Troubleshooting

### CUDA not available
```bash
# Check CUDA installation
nvidia-smi

# Install CUDA toolkit (if needed)
sudo apt install nvidia-cuda-toolkit
```

### Port already in use
```bash
# Check what's using port 8000
sudo lsof -i :8000

# Or change port in config.yaml
```

### Model download fails
Models download from HuggingFace automatically. If it fails:
```bash
# Manual download to models/ directory
mkdir -p models
wget https://huggingface.co/guillaumekln/faster-whisper-medium/resolve/main/model.bin
```

## Firewall

If the client is on a different machine, allow port 8000:

```bash
sudo ufw allow 8000/tcp
# Or for specific IP only
sudo ufw allow from 10.0.0.0/24 to any port 8000
```
