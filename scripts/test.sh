#!/bin/bash
set -e

# Navigate to project root
cd "$(dirname "$0")/.."

BASE_URL="http://localhost:8000"
TEMP_DIR="/tmp/tts-test-$$"
mkdir -p "$TEMP_DIR"

echo "==================================="
echo "Testing Kokoro TTS Service"
echo "==================================="
echo ""

# Test 1: Check if service is running
echo "[1/5] Testing service availability..."
if curl -f -s "${BASE_URL}/v1/models" > /dev/null 2>&1; then
    echo "✅ Service is running"
else
    echo "❌ Service is not responding"
    echo "   Make sure the service is started: ./scripts/start.sh"
    exit 1
fi

# Test 2: List models endpoint
echo ""
echo "[2/5] Testing /v1/models endpoint..."
MODELS_RESPONSE=$(curl -s "${BASE_URL}/v1/models")
if echo "$MODELS_RESPONSE" | grep -q "tts-1"; then
    echo "✅ Models endpoint working"
    echo "   Found models: $(echo "$MODELS_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 | tr '\n' ' ')"
else
    echo "❌ Models endpoint failed"
    echo "   Response: $MODELS_RESPONSE"
    exit 1
fi

# Test 3: List voices endpoint
echo ""
echo "[3/5] Testing /v1/audio/voices endpoint..."
VOICES_RESPONSE=$(curl -s "${BASE_URL}/v1/audio/voices")
if echo "$VOICES_RESPONSE" | grep -q "voices"; then
    echo "✅ Voices endpoint working"
    # Count voices
    VOICE_COUNT=$(echo "$VOICES_RESPONSE" | grep -o '"id"' | wc -l)
    echo "   Found $VOICE_COUNT voices available"
else
    echo "❌ Voices endpoint failed"
    echo "   Response: $VOICES_RESPONSE"
    exit 1
fi

# Test 4: Generate speech (MP3 format)
echo ""
echo "[4/5] Testing speech generation (MP3)..."
START_TIME=$(date +%s%N)
HTTP_CODE=$(curl -X POST "${BASE_URL}/v1/audio/speech" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "tts-1",
        "input": "This is a test of the Kokoro text to speech service.",
        "voice": "af_alloy",
        "response_format": "mp3"
    }' \
    --output "${TEMP_DIR}/test.mp3" \
    -w "%{http_code}" \
    -s)
END_TIME=$(date +%s%N)
DURATION_MS=$(( (END_TIME - START_TIME) / 1000000 ))

if [ "$HTTP_CODE" -eq 200 ] && [ -f "${TEMP_DIR}/test.mp3" ]; then
    FILE_SIZE=$(stat -c%s "${TEMP_DIR}/test.mp3")
    if [ "$FILE_SIZE" -gt 1000 ]; then
        echo "✅ Speech generation successful"
        echo "   File size: ${FILE_SIZE} bytes"
        echo "   Generation time: ${DURATION_MS}ms"

        # Calculate RTF (Real-Time Factor) - approximate
        # Assuming ~150 words per minute reading speed
        TEXT_LENGTH=11  # words in test text
        ESTIMATED_AUDIO_DURATION=$((TEXT_LENGTH * 60 / 150))  # seconds
        if [ "$ESTIMATED_AUDIO_DURATION" -gt 0 ]; then
            RTF=$(echo "scale=2; $DURATION_MS / ($ESTIMATED_AUDIO_DURATION * 1000)" | bc)
            echo "   Estimated RTF: ${RTF} (lower is better, <1.0 is real-time)"
        fi
    else
        echo "❌ Generated file is too small (${FILE_SIZE} bytes)"
        exit 1
    fi
else
    echo "❌ Speech generation failed (HTTP ${HTTP_CODE})"
    exit 1
fi

# Test 5: Test different voice
echo ""
echo "[5/5] Testing voice selection..."
HTTP_CODE=$(curl -X POST "${BASE_URL}/v1/audio/speech" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "tts-1",
        "input": "Testing a different voice.",
        "voice": "af_bella",
        "response_format": "mp3"
    }' \
    --output "${TEMP_DIR}/test_bella.mp3" \
    -w "%{http_code}" \
    -s)

if [ "$HTTP_CODE" -eq 200 ] && [ -f "${TEMP_DIR}/test_bella.mp3" ]; then
    FILE_SIZE=$(stat -c%s "${TEMP_DIR}/test_bella.mp3")
    if [ "$FILE_SIZE" -gt 1000 ]; then
        echo "✅ Voice selection working"
        echo "   Generated with 'af_bella' voice: ${FILE_SIZE} bytes"
    else
        echo "❌ Generated file is too small (${FILE_SIZE} bytes)"
        exit 1
    fi
else
    echo "❌ Voice selection test failed (HTTP ${HTTP_CODE})"
    exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "==================================="
echo "✅ All Tests Passed!"
echo "==================================="
echo ""
echo "Service is working correctly on port 8000"
echo ""
echo "Test files were generated successfully and cleaned up."
echo ""
