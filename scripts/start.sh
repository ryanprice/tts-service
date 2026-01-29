#!/bin/bash
set -e

# Navigate to project root
cd "$(dirname "$0")/.."

echo "==================================="
echo "Starting Kokoro TTS Service"
echo "==================================="

# Check if image exists, pull if not
if [ ! "$(docker images -q dustynv/kokoro-tts:fastapi-r36.4.0 2> /dev/null)" ]; then
    echo "Docker image not found. Pulling..."
    ./scripts/build.sh
fi

# Start the service
echo "Starting service..."
docker compose up -d

# Wait for health check
echo ""
echo "Waiting for service to be ready..."
TIMEOUT=120
ELAPSED=0
INTERVAL=5

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Check if container is running
    if ! docker ps | grep -q "kokoro-tts-service"; then
        echo "❌ Container stopped unexpectedly"
        echo ""
        echo "Logs:"
        docker compose logs --tail=50
        exit 1
    fi

    # Check if service responds
    if curl -f -s http://localhost:8000/v1/models > /dev/null 2>&1; then
        echo ""
        echo "==================================="
        echo "✅ Service Ready!"
        echo "==================================="
        echo ""
        echo "Service URLs:"
        echo "  API Base:    http://localhost:8000"
        echo "  Web UI:      http://localhost:8000/web"
        echo "  API Docs:    http://localhost:8000/docs"
        echo "  Models:      http://localhost:8000/v1/models"
        echo "  Voices:      http://localhost:8000/v1/audio/voices"
        echo ""
        echo "Quick test:"
        echo '  curl -X POST http://localhost:8000/v1/audio/speech \\'
        echo '    -H "Content-Type: application/json" \\'
        echo '    -d '"'"'{"model": "tts-1", "input": "Hello!", "voice": "alloy", "response_format": "mp3"}'"'"' \\'
        echo '    --output test.mp3'
        echo ""
        exit 0
    fi

    echo -n "."
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""
echo "❌ Service failed to start within ${TIMEOUT}s"
echo ""
echo "Container status:"
docker compose ps
echo ""
echo "Recent logs:"
docker compose logs --tail=50
exit 1
