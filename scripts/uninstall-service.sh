#!/bin/bash
# Uninstall Kokoro TTS systemd service

set -e

SERVICE_NAME="kokoro-tts"

echo "Uninstalling Kokoro TTS systemd service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo $0"
    exit 1
fi

# Stop service if running
if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl stop "$SERVICE_NAME"
    echo "Stopped $SERVICE_NAME"
fi

# Disable service
if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    systemctl disable "$SERVICE_NAME"
    echo "Disabled $SERVICE_NAME"
fi

# Remove service file
if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    rm "/etc/systemd/system/${SERVICE_NAME}.service"
    echo "Removed service file"
fi

# Reload systemd
systemctl daemon-reload
echo "Reloaded systemd daemon"

echo ""
echo "Uninstallation complete!"
echo "The Docker containers are still available - use docker compose manually if needed."
