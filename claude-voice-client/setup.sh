#!/bin/bash
# Setup script for Claude Voice Client

set -e

echo "================================"
echo "Claude Voice Client Setup"
echo "================================"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Install system dependencies
echo ""
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y portaudio19-dev python3-pip python3-venv

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install pyaudio pynput requests pyyaml colorama

# Check audio devices
echo ""
echo "Checking audio devices..."
python3 -c "
import pyaudio
p = pyaudio.PyAudio()
print(f'Found {p.get_device_count()} audio devices')
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'  [{i}] {info[\"name\"]} ({info[\"maxInputChannels\"]} channels)')
p.terminate()
"

echo ""
echo "================================"
echo "Setup complete!"
echo "================================"
echo ""
echo "To start the client:"
echo "  source venv/bin/activate"
echo "  python src/main.py"
echo ""
echo "Press Ctrl+Shift+V to start/stop recording"
echo ""
