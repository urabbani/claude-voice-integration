# Claude Voice Integration - Installation Guide

Complete guide to setting up voice input for Claude Code using a client-server architecture with GPU-accelerated transcription.

## Architecture Overview

```
┌─────────────────────────┐         ┌──────────────────────────┐
│   Client Machine        │         │   Server Machine         │
│   (WSL Ubuntu)          │         │   (WSL Ubuntu + RTX5090) │
├─────────────────────────┤         ├──────────────────────────┤
│ • Captures microphone   │         │ • faster-whisper (CUDA)  │
│ • Sends audio           │ ───────▶ │ • RTX 5090 GPU          │
│ • Receives text         │         │ • Returns transcription  │
│ • Copies to clipboard   │         │                          │
└─────────────────────────┘         └──────────────────────────┘
        IP: <any>                          IP: 10.0.0.205
```

## Prerequisites

### Both Machines
- WSL Ubuntu on Windows 11
- Python 3.9+
- Network connectivity between machines

### Server Machine (RTX 5090)
- NVIDIA GPU with CUDA support
- nvidia-smi working

### Client Machine
- Microphone accessible from WSL
- PulseAudio working

---

## Part 1: Server Setup (RTX 5090 Machine - 10.0.0.205)

### Step 1: Copy Files

Transfer the `claude-voice-server` directory to your RTX 5090 machine:

```bash
# From client machine, run:
scp -r /mnt/d/clauder/claude-voice-server user@10.0.0.205:~/

# Or use rsync:
rsync -av /mnt/d/clauder/claude-voice-server/ user@10.0.0.205:~/claude-voice-server/
```

### Step 2: Run Setup Script

On the **server machine** (10.0.0.205):

```bash
cd ~/claude-voice-server
./setup.sh
```

### Step 3: Test Server

```bash
source venv/bin/activate
python -m uvicorn src.server:app --host 0.0.0.0 --port 8000
```

The first run will download the Whisper medium model (~769MB).

### Step 4: Enable Auto-Start (Optional)

```bash
./install-service.sh
```

### Step 5: Verify

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","model":"medium","device":"cuda"}
```

---

## Part 2: Client Setup (Your WSL Machine)

### Step 1: Run Setup Script

```bash
cd ~/claude-voice-client
./setup.sh
```

### Step 2: Test Audio Devices

```bash
source venv/bin/activate
python src/main.py --test-audio
```

### Step 3: Run Client

```bash
source venv/bin/activate
python src/main.py
```

### Step 4: Test Recording

1. Press `Ctrl+Shift+V` to start recording
2. Speak: "Hello world, this is a test"
3. Press `Ctrl+Shift+V` to stop
4. Text should appear and be copied to clipboard

---

## Part 3: Usage with Claude Code

### Method 1: Manual Paste

1. Start voice client in a separate terminal
2. Use hotkey to dictate your prompt
3. Paste text into Claude Code with `Ctrl+Shift+V`

### Method 2: Auto-Start in Shell

Add to `~/.bashrc`:

```bash
# Claude Voice Client
if [ -f ~/claude-voice-client/venv/bin/activate ]; then
    # Start in background with nohup
    (
        source ~/claude-voice-client/venv/bin/activate
        nohup python ~/claude-voice-client/src/main.py > ~/.claude-voice.log 2>&1 &
    ) &
fi
```

---

## Troubleshooting

### Server Issues

**Problem: CUDA not available**
```bash
# Check GPU
nvidia-smi

# Install CUDA toolkit
sudo apt install nvidia-cuda-toolkit
```

**Problem: Port 8000 already in use**
```bash
# Check what's using the port
sudo lsof -i :8000

# Change port in config.yaml
```

### Client Issues

**Problem: No audio devices found**
```bash
# Check PulseAudio
pactl info

# List microphones
pacmd list-sources

# Restart PulseAudio
pulseaudio --kill
pulseaudio --start
```

**Problem: Server unreachable**
```bash
# Test connectivity
ping 10.0.0.205

# Test server
curl http://10.0.0.205:8000/health

# Check firewall on server
sudo ufw allow 8000/tcp
```

**Problem: Hotkey not working**
- Try a different hotkey in `config.yaml`
- Check for conflicts with other apps
- Make sure terminal isn't capturing the hotkey

---

## Configuration

### Client Config (`~/claude-voice-client/config.yaml`)

```yaml
hotkey: "ctrl+shift+v"           # Global hotkey
server_url: "http://10.0.0.205:8000"  # Server IP
audio:
  max_duration: 30                # Max recording (seconds)
```

### Server Config (`~/claude-voice-server/config.yaml`)

```yaml
model:
  name: "medium"                  # Model: tiny, base, small, medium, large-v3
  compute_type: "float16"         # Use float16 for RTX 5090
```

---

## Performance

| Model | VRAM | Latency | Accuracy |
|-------|------|---------|----------|
| tiny | 1GB | ~200ms | Fair |
| base | 1GB | ~300ms | Good |
| small | 2GB | ~500ms | Very Good |
| medium | 5GB | ~1s | Excellent |
| large-v3 | 10GB | ~2s | Best |

**Recommended:** `medium` for RTX 5090

---

## Next Steps

1. **Test with Claude Code** — Try dictating a complex prompt
2. **Customize hotkey** — Change to your preference
3. **Add auto-start** — Configure both services to start on boot
4. **Monitor performance** — Check server logs for optimization

---

## Support

For issues or questions:
- Check logs: `journalctl --user -u claude-voice-server`
- Test server: `curl http://10.0.0.205:8000/health`
- Test audio: `python src/main.py --test-audio`
