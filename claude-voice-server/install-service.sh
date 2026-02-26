#!/bin/bash
# Install systemd user service for auto-start

set -e

SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="claude-voice-server.service"
INSTALL_DIR="$(pwd)"

echo "Installing systemd service..."

# Create service directory
mkdir -p "$SERVICE_DIR"

# Create service file
cat > "$SERVICE_DIR/$SERVICE_FILE" << EOF
[Unit]
Description=Claude Voice STT Server
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python -m uvicorn src.server:app --host 0.0.0.0 --port 8000
Restart=always
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/bin

[Install]
WantedBy=default.target
EOF

# Reload systemd
systemctl --user daemon-reload

# Enable service
echo "Enabling service..."
systemctl --user enable claude-voice-server

# Start service
echo "Starting service..."
systemctl --user start claude-voice-server

# Show status
echo ""
echo "Service status:"
systemctl --user status claude-voice-server --no-pager

echo ""
echo "================================"
echo "Service installed and started!"
echo "================================"
echo ""
echo "Commands:"
echo "  systemctl --user start claude-voice-server    # Start"
echo "  systemctl --user stop claude-voice-server     # Stop"
echo "  systemctl --user restart claude-voice-server  # Restart"
echo "  systemctl --user status claude-voice-server   # Status"
echo "  journalctl --user -u claude-voice-server      # Logs"
echo ""
