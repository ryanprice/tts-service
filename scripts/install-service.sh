#!/bin/bash
# Install Kokoro TTS as a systemd service

set -e

SERVICE_NAME="kokoro-tts"
SERVICE_FILE="/home/rprice/myapplications/tts-service/kokoro-tts.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "Installing Kokoro TTS systemd service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo $0"
    exit 1
fi

# Copy service file
cp "$SERVICE_FILE" "$SYSTEMD_DIR/${SERVICE_NAME}.service"
echo "Copied service file to $SYSTEMD_DIR"

# Reload systemd
systemctl daemon-reload
echo "Reloaded systemd daemon"

# Enable service to start on boot
systemctl enable "$SERVICE_NAME"
echo "Enabled $SERVICE_NAME to start on boot"

echo ""
echo "Installation complete!"
echo ""
echo "Commands:"
echo "  sudo systemctl start $SERVICE_NAME    # Start the service"
echo "  sudo systemctl stop $SERVICE_NAME     # Stop the service"
echo "  sudo systemctl restart $SERVICE_NAME  # Restart the service"
echo "  sudo systemctl status $SERVICE_NAME   # Check status"
echo "  journalctl -u $SERVICE_NAME -f        # View logs"
echo ""
echo "The service will now start automatically on boot."
