#!/bin/bash
# Setup script for Claude Voice STT Server

set -e

echo "================================"
echo "Claude Voice STT Server Setup"
echo "================================"
echo ""

# Check NVIDIA GPU
echo "Checking for NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo ""
else
    echo "Warning: nvidia-smi not found. Make sure CUDA is installed."
    echo ""
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn[standard] faster-whisper pyyaml python-multipart

# Create models directory
mkdir -p models

echo ""
echo "================================"
echo "Setup complete!"
echo "================================"
echo ""
echo "The Whisper model will be downloaded on first run."
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python -m uvicorn src.server:app --host 0.0.0.0 --port 8000"
echo ""
echo "To enable auto-start (systemd):"
echo "  ./install-service.sh"
echo ""
