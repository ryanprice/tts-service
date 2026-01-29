#!/bin/bash
set -e

# Navigate to project root
cd "$(dirname "$0")/.."

echo "Stopping Kokoro TTS Service..."

docker compose down

if [ $? -eq 0 ]; then
    echo "✅ Service stopped successfully"
else
    echo "❌ Failed to stop service"
    exit 1
fi
