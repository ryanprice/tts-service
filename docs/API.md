# Kokoro TTS Service - API Reference

Complete API documentation for the Kokoro TTS Service running on port 8000.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. The service is designed for local/internal use.

## Endpoints

### 1. Generate Speech

Generate speech audio from text input.

**Endpoint**: `POST /v1/audio/speech`

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "model": "tts-1",
  "input": "Text to convert to speech",
  "voice": "alloy",
  "response_format": "mp3",
  "speed": 1.0
}
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | string | Yes | - | Model ID (use `"tts-1"`) |
| `input` | string | Yes | - | Text to synthesize (max ~500 words) |
| `voice` | string | No | `"af_alloy"` | Voice ID (see available voices below) |
| `response_format` | string | No | `"mp3"` | Audio format: `mp3`, `wav`, `opus`, `flac` |
| `speed` | number | No | `1.0` | Speech speed (0.5 to 2.0) |

**Response**:
- **Status**: `200 OK`
- **Content-Type**: `audio/mpeg` (or appropriate audio type)
- **Body**: Binary audio data

**Example Request**:
```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello, how are you today?",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output speech.mp3
```

**Example Response**:
Binary MP3 audio data

**Error Responses**:
- `400 Bad Request` - Invalid parameters
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

### 2. List Models

Get list of available TTS models.

**Endpoint**: `GET /v1/models`

**Request Headers**: None required

**Response**:
```json
{
  "data": [
    {
      "id": "tts-1",
      "object": "model",
      "created": 1234567890,
      "owned_by": "kokoro"
    }
  ]
}
```

**Example Request**:
```bash
curl http://localhost:8000/v1/models
```

---

### 3. List Available Voices

Get list of all available voices with metadata.

**Endpoint**: `GET /v1/audio/voices`

**Request Headers**: None required

**Response**:
```json
{
  "voices": [
    {
      "id": "af_alloy",
      "name": "Alloy",
      "language": "en",
      "gender": "neutral"
    },
    {
      "id": "af_bella",
      "name": "Bella",
      "language": "en",
      "gender": "female"
    }
  ]
}
```

**Example Request**:
```bash
curl http://localhost:8000/v1/audio/voices
```

---

### 4. Web Interface

Access the web-based testing interface.

**Endpoint**: `GET /web`

**Description**: Interactive web UI for testing TTS functionality

**URL**: http://localhost:8000/web

---

### 5. API Documentation

Interactive API documentation (Swagger UI).

**Endpoint**: `GET /docs`

**Description**: Auto-generated API documentation with interactive testing

**URL**: http://localhost:8000/docs

---

## Available Voices

### English Voices

| Voice ID | Short Name | Gender | Description |
|----------|------------|--------|-------------|
| `af_alloy` | `alloy` | Neutral | Balanced, clear voice suitable for general purposes |
| `af_bella` | `bella` | Female | Warm, friendly female voice |
| `af_nova` | `nova` | Neutral | Modern, energetic voice |
| `af_shimmer` | `shimmer` | Female | Bright, expressive voice |
| `af_echo` | `echo` | Male | Deep, authoritative male voice |
| `af_onyx` | `onyx` | Male | Smooth, professional male voice |

### Japanese Voices

| Voice ID | Language | Description |
|----------|----------|-------------|
| `ja_alloy` | Japanese | Japanese version of Alloy |
| `ja_bella` | Japanese | Japanese version of Bella |
| `ja_nova` | Japanese | Japanese version of Nova |

### Chinese Voices

| Voice ID | Language | Description |
|----------|----------|-------------|
| `zh_alloy` | Chinese | Chinese version of Alloy |
| `zh_bella` | Chinese | Chinese version of Bella |

**Note**: Query `/v1/audio/voices` for the most current list of available voices.

---

## Audio Formats

| Format | Extension | MIME Type | Description |
|--------|-----------|-----------|-------------|
| MP3 | `.mp3` | `audio/mpeg` | Compressed, widely compatible (default) |
| WAV | `.wav` | `audio/wav` | Uncompressed, high quality |
| OPUS | `.opus` | `audio/opus` | Modern, efficient codec |
| FLAC | `.flac` | `audio/flac` | Lossless compression |

---

## Code Examples

### Python

```python
import requests

def generate_speech(text, voice="alloy", output_file="speech.mp3"):
    """Generate speech from text"""
    url = "http://localhost:8000/v1/audio/speech"

    payload = {
        "model": "tts-1",
        "input": text,
        "voice": voice,
        "response_format": "mp3"
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"Speech saved to {output_file}")
        return True
    else:
        print(f"Error: {response.status_code}")
        return False

# Usage
generate_speech("Hello, this is a test!", voice="bella")
```

### JavaScript (Node.js)

```javascript
const fs = require('fs');
const axios = require('axios');

async function generateSpeech(text, voice = 'alloy', outputFile = 'speech.mp3') {
  const url = 'http://localhost:8000/v1/audio/speech';

  const payload = {
    model: 'tts-1',
    input: text,
    voice: voice,
    response_format: 'mp3'
  };

  try {
    const response = await axios.post(url, payload, {
      responseType: 'arraybuffer'
    });

    fs.writeFileSync(outputFile, response.data);
    console.log(`Speech saved to ${outputFile}`);
    return true;
  } catch (error) {
    console.error('Error:', error.message);
    return false;
  }
}

// Usage
generateSpeech('Hello, this is a test!', 'bella');
```

### cURL

```bash
# Basic usage
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello world!",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output speech.mp3

# With different voice
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "This is Bella speaking.",
    "voice": "bella",
    "response_format": "mp3"
  }' \
  --output bella.mp3

# WAV format
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "High quality audio.",
    "voice": "alloy",
    "response_format": "wav"
  }' \
  --output speech.wav

# Japanese
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "こんにちは、元気ですか？",
    "voice": "ja_bella",
    "response_format": "mp3"
  }' \
  --output japanese.mp3
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "message": "Error description",
    "type": "invalid_request_error",
    "code": "invalid_parameter"
  }
}
```

### Common Error Codes

| Status Code | Type | Description | Solution |
|-------------|------|-------------|----------|
| 400 | Bad Request | Invalid request format | Check request JSON structure |
| 422 | Validation Error | Invalid parameter values | Verify all parameters are valid |
| 500 | Internal Error | Server processing error | Check logs, retry request |
| 503 | Service Unavailable | Service not ready | Wait for service startup |

### Example Error Handling (Python)

```python
import requests

def safe_generate_speech(text, voice="alloy"):
    """Generate speech with error handling"""
    url = "http://localhost:8000/v1/audio/speech"

    payload = {
        "model": "tts-1",
        "input": text,
        "voice": voice,
        "response_format": "mp3"
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        return response.content

    except requests.exceptions.Timeout:
        print("Request timeout - text may be too long")
        return None

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print("Bad request - check parameters")
        elif e.response.status_code == 422:
            print("Validation error:", e.response.json())
        else:
            print(f"HTTP error: {e.response.status_code}")
        return None

    except requests.exceptions.ConnectionError:
        print("Cannot connect to service - is it running?")
        return None
```

---

## Rate Limiting

Currently no rate limiting is enforced. However, concurrent requests are limited by:
- Docker resource limits
- GPU memory availability
- Configured `MAX_CONCURRENT_REQUESTS` (default: 2)

For best performance, limit to 2-4 concurrent requests.

---

## Performance Metrics

### Typical Response Times

| Text Length | Generation Time | RTF |
|-------------|----------------|-----|
| Short (1-10 words) | 0.2-0.5s | 0.1-0.3 |
| Medium (10-50 words) | 0.5-2s | 0.2-0.5 |
| Long (50-200 words) | 2-8s | 0.3-0.7 |

**RTF (Real-Time Factor)**: Ratio of generation time to audio duration. RTF < 1.0 means faster than real-time.

### Best Practices

1. **Optimal text length**: 10-100 words per request
2. **Concurrent requests**: Limit to 2-4 simultaneous
3. **Format selection**: Use MP3 for smallest files, WAV for quality
4. **Error handling**: Always implement timeout and retry logic
5. **Voice selection**: Cache `/v1/audio/voices` response

---

## OpenAI Compatibility

This API is designed to be compatible with OpenAI's Text-to-Speech API. You can often use it as a drop-in replacement by changing the base URL.

### OpenAI Python SDK Example

```python
from openai import OpenAI

# Point to local TTS service
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # API key not required for local service
)

response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello from the local TTS service!"
)

response.stream_to_file("speech.mp3")
```

---

## Health Checks

### Service Health

Check if service is ready:

```bash
curl -f http://localhost:8000/v1/models
```

If this returns HTTP 200, the service is ready to accept requests.

### Monitor Performance

Check GPU usage:
```bash
nvidia-smi
```

Check Docker stats:
```bash
docker stats kokoro-tts-service
```

---

## Troubleshooting API Issues

### Request Fails with Timeout

- **Cause**: Text too long or service overloaded
- **Solution**: Reduce text length, wait for current requests to complete

### Audio Quality Poor

- **Cause**: Wrong format or voice selection
- **Solution**: Try `wav` format, test different voices

### Service Returns 503

- **Cause**: Service still starting up
- **Solution**: Wait 30-60s after `docker compose up`

### Incorrect Voice

- **Cause**: Voice ID typo or unsupported voice
- **Solution**: Query `/v1/audio/voices` for valid voice IDs

---

## API Versioning

Current API version: `v1`

All endpoints are prefixed with `/v1/` to allow for future API versions.

---

## Support

For additional help:
- Interactive docs: http://localhost:8000/docs
- Service logs: `docker compose logs -f`
- Test script: `./scripts/test.sh`
