#!/bin/bash
set -e

# Navigate to project root
cd "$(dirname "$0")/.."

echo "==================================="
echo "Pulling Kokoro TTS Image"
echo "==================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

echo "✅ Docker is running"

# Pull the pre-built Docker image
echo ""
echo "Pulling pre-built Kokoro TTS image from Docker Hub..."
echo "This may take a few minutes (~2-3GB download)..."
echo ""

docker compose pull

if [ $? -eq 0 ]; then
    echo ""
    echo "==================================="
    echo "✅ Image Pulled Successfully!"
    echo "==================================="
    echo ""
    echo "Next steps:"
    echo "  ./scripts/start.sh  - Start the TTS service"
    echo "  ./scripts/test.sh   - Test the service"
else
    echo ""
    echo "❌ Pull failed"
    exit 1
fi
