# TTS Service with Whisper Alignment

A text-to-speech service with word-level alignment, running on Jetson Nano Orin (8GB VRAM). Combines Kokoro TTS (GPU) with Whisper alignment (CPU) via a FastAPI gateway.

<img width="1270" height="880" alt="image" src="https://github.com/user-attachments/assets/e17fbf15-51c2-495e-9cf4-9a14d87d6840" />

## Features

- High-quality text-to-speech using Kokoro/FastKoko
- Word-level timestamp alignment using faster-whisper
- Combined endpoint: TTS + alignment in one request
- Multiple voices in English, Japanese, and Chinese
- Multiple formats (MP3, WAV, OPUS, FLAC)
- GPU-accelerated TTS on NVIDIA Jetson
- CPU-based Whisper alignment (preserves GPU for TTS)
- OpenAI-compatible API for easy integration
- Web UI for testing and demos
- Real-time performance (RTF 0.26 - 4x faster than real-time!)

## Overview

This implementation uses the pre-built `dustynv/kokoro-tts:fastapi-r36.4.0` Docker image (11.6GB) from the [jetson-containers](https://github.com/dusty-nv/jetson-containers) project. The service:

- Listens on **port 8000** (mapped from internal port 8880)
- Provides an **OpenAI-compatible API** for easy integration
- Includes a **web UI** for testing at http://localhost:8000/web
- Runs entirely on your **local Jetson device** with GPU acceleration
- Requires **no API keys or cloud services**

## Quick Start

### 1. Pull the Image

```bash
./scripts/build.sh
```

> **Note**: This downloads the pre-built image `dustynv/kokoro-tts:fastapi-r36.4.0` (~11.6GB) from Docker Hub. First download may take 10-30 minutes depending on your internet connection.

### 2. Start the Service

```bash
./scripts/start.sh
```

The service will start on **http://localhost:8000**

### 3. Test the Service

```bash
./scripts/test.sh
```

Or run Python tests:

```bash
python3 tests/test_api.py
```

### 4. Generate Your First Speech

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "tts-1", "input": "Hello world", "voice": "alloy", "response_format": "mp3"}' \
  --output hello.mp3
```

Play the file with: `mpg123 hello.mp3` or any audio player.

> **Note**: You may see a warning about `version` in docker-compose.yml - this is harmless and can be ignored.

## Usage

### Web UI

Open your browser and navigate to:
- **Web Interface**: http://localhost:8000/web
- **API Documentation**: http://localhost:8000/docs

### API Endpoints

#### Generate Speech

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello from Kokoro TTS!",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output speech.mp3
```

#### List Available Voices

```bash
curl http://localhost:8000/v1/audio/voices
```

#### List Available Models

```bash
curl http://localhost:8000/v1/models
```

#### Get Word Alignment (from existing audio)

```bash
# First, base64 encode your audio file
AUDIO_B64=$(base64 -w 0 speech.mp3)

curl -X POST http://localhost:8000/v1/audio/align \
  -H "Content-Type: application/json" \
  -d "{\"audio_file\": \"$AUDIO_B64\"}"
```

Response:
```json
{
  "words": [
    {"word": "Hello", "start": 0.0, "end": 0.32},
    {"word": "world", "start": 0.35, "end": 0.72}
  ]
}
```

#### Generate Speech WITH Alignment (Combined - Recommended)

```bash
curl -X POST http://localhost:8000/v1/audio/speech_with_alignment \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello world",
    "voice": "alloy",
    "response_format": "mp3"
  }'
```

Response:
```json
{
  "audio": "base64_encoded_mp3",
  "words": [
    {"word": "Hello", "start": 0.0, "end": 0.32},
    {"word": "world", "start": 0.35, "end": 0.72}
  ],
  "format": "mp3"
}
```

### Python Example

```python
import requests

url = "http://localhost:8000/v1/audio/speech"
payload = {
    "model": "tts-1",
    "input": "Hello, this is a test of the TTS service.",
    "voice": "alloy",
    "response_format": "mp3"
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    with open("output.mp3", "wb") as f:
        f.write(response.content)
    print("Speech generated successfully!")
```

## Available Voices

The service supports multiple voices across different languages:

### English Voices (Tested ✅)
- `af_alloy` / `alloy` - Balanced, neutral voice ✅
- `af_bella` / `bella` - Warm, friendly female voice ✅
- `af_nova` / `nova` - Modern, energetic voice
- `af_shimmer` / `shimmer` - Bright, expressive voice
- `af_echo` / `echo` - Deep, authoritative male voice
- `af_onyx` / `onyx` - Smooth, professional male voice

### Other Languages
- **Japanese**: `ja_alloy`, `ja_bella`, `ja_nova`, etc.
- **Chinese**: `zh_alloy`, `zh_bella`, etc.

> **Tip**: Both full names (`af_alloy`) and short names (`alloy`) work. Query `/v1/audio/voices` for the complete current list.

### Available Models

- `tts-1` - Standard quality (recommended)
- `tts-1-hd` - High definition quality
- `kokoro` - Native Kokoro model

## Supported Audio Formats

- `mp3` (default) - MPEG Audio Layer III
- `wav` - Waveform Audio File Format
- `opus` - Opus codec
- `flac` - Free Lossless Audio Codec

## Service Management

### Start Service
```bash
./scripts/start.sh
```

### Stop Service
```bash
./scripts/stop.sh
```

### View Logs
```bash
docker compose logs -f
```

### Restart Service
```bash
./scripts/stop.sh && ./scripts/start.sh
```

### Run as systemd Service

To have the TTS service start automatically on boot, install it as a systemd service:

```bash
sudo ./scripts/install-service.sh
```

Then manage it with standard systemctl commands:

```bash
# Start the service
sudo systemctl start kokoro-tts

# Stop the service
sudo systemctl stop kokoro-tts

# Restart the service
sudo systemctl restart kokoro-tts

# Check status
sudo systemctl status kokoro-tts

# View logs
journalctl -u kokoro-tts -f
```

To uninstall the systemd service:

```bash
sudo ./scripts/uninstall-service.sh
```

## Performance

Optimized for Jetson Nano Orin with 8GB VRAM:

- **VRAM Usage**: Minimal (GPU memory freed between requests)
- **Real-Time Factor**: ~0.26 (4x faster than real-time) ⚡
- **Generation Speed**: ~1 second for short phrases, 1-2 seconds for longer text
- **Startup Time**: 30-60 seconds
- **Concurrent Requests**: Up to 2-4 simultaneous
- **File Sizes**: ~17KB for "Hello world", ~144KB for 30-word paragraph

### Actual Test Results

```
Test: "This is a test of the Kokoro text to speech service."
- File size: 41.9KB
- Generation time: 1079ms
- RTF: 0.26 (faster than real-time)
- Format: MP3, 24kHz, mono
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Your Application                │
└──────────────┬──────────────────────────┘
               │ HTTP (Port 8000)
               ▼
┌─────────────────────────────────────────────────────────┐
│           TTS Gateway (FastAPI)                         │
│  ┌───────────────────┐    ┌─────────────────────────┐  │
│  │  TTS Proxy        │    │  Whisper Alignment      │  │
│  │  /v1/audio/speech │    │  /v1/audio/align        │  │
│  └─────────┬─────────┘    │  (CPU - faster-whisper) │  │
│            │              └─────────────────────────┘  │
│            │              ┌─────────────────────────┐  │
│            │              │  Combined Endpoint      │  │
│            │              │  /v1/audio/speech_with_ │  │
│            │              │  alignment              │  │
│            │              └─────────────────────────┘  │
└────────────┼───────────────────────────────────────────┘
             │ Internal (Port 8880)
             ▼
┌─────────────────────────────────────────┐
│     Kokoro TTS Backend (Docker)         │
│  ┌────────────────────────────────────┐ │
│  │    Kokoro TTS Model (PyTorch)      │ │
│  │         + GPU Acceleration         │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Directory Structure

```
tts-service/
├── docker-compose.yml          # Service orchestration (gateway + TTS)
├── kokoro-tts.service          # systemd unit file
├── .env                        # Environment configuration
├── README.md                   # This file
├── gateway/                    # TTS Gateway with Whisper
│   ├── main.py                # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Gateway container
├── config/
│   └── voices.json            # Voice metadata
├── scripts/
│   ├── build.sh               # Build service
│   ├── start.sh               # Start service
│   ├── stop.sh                # Stop service
│   ├── test.sh                # Run tests
│   ├── install-service.sh     # Install systemd service
│   └── uninstall-service.sh   # Uninstall systemd service
├── tests/
│   └── test_api.py            # Python API tests
├── docs/
│   └── API.md                 # API documentation
├── models/                     # Model storage (auto-populated)
├── audio/                      # Generated audio output
└── logs/                       # Service logs
```

## Configuration

### Environment Variables

Edit `.env` to customize:

```bash
# Service Configuration
SERVICE_PORT=8000              # External port
USE_GPU=true                   # Enable GPU acceleration
USE_ONNX=false                 # Use PyTorch (better for 8GB VRAM)

# Whisper Configuration (for word alignment)
# Options: tiny, base, small, medium, large-v3
# tiny: ~39MB, fastest, good for TTS alignment
# base: ~74MB, balanced
# small: ~244MB, better accuracy
WHISPER_MODEL=tiny             # Recommended for Jetson

# Resource Limits
MAX_CONCURRENT_REQUESTS=2      # Concurrent request limit
GPU_MEMORY_FRACTION=0.7        # GPU memory allocation
```

### Docker Compose

Edit `docker-compose.yml` to adjust:
- Memory limits
- Volume mounts
- Port mappings
- GPU device access

## Troubleshooting

### Service Won't Start

1. Check if Docker is running:
   ```bash
   docker info
   ```

2. Check NVIDIA runtime:
   ```bash
   docker run --rm --runtime=nvidia nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi
   ```

3. View logs:
   ```bash
   docker compose logs
   ```

### Low Performance

1. Check GPU usage:
   ```bash
   nvidia-smi
   ```

2. Verify GPU is enabled in `.env`:
   ```bash
   USE_GPU=true
   USE_ONNX=false
   ```

3. Reduce concurrent requests in `.env`:
   ```bash
   MAX_CONCURRENT_REQUESTS=1
   ```

### Out of Memory

1. Lower memory limits in `docker-compose.yml`
2. Reduce concurrent requests
3. Check other GPU processes: `nvidia-smi`

### Audio Quality Issues

1. Try different voices: `/v1/audio/voices`
2. Use lossless format: `"response_format": "wav"`
3. Check input text formatting

### JSON Errors (422 Unprocessable Entity)

If you get JSON decode errors with special characters:

1. **Avoid special characters** in curl commands that need escaping (like apostrophes, quotes)
2. **Use simple text** for testing: `"Hello world"` works better than complex sentences
3. **For complex text**, save JSON to a file and use: `curl -X POST http://localhost:8000/v1/audio/speech -H "Content-Type: application/json" -d @request.json --output output.mp3`
4. **In Python/JavaScript**, use proper JSON libraries that handle escaping automatically

### Version Warning

The warning `"the attribute 'version' is obsolete"` from docker-compose is harmless and can be safely ignored. It's a deprecation notice for the `version:` field in docker-compose.yml.

## API Reference

See [docs/API.md](docs/API.md) for complete API documentation.

## Requirements

### Hardware
- **Jetson Nano Orin** with 8GB VRAM (or compatible Jetson device)
- **At least 20GB free storage** for Docker image (11.6GB) and generated audio
- **Internet connection** for initial image download

### Software
- **Docker** >= 20.10 with Compose plugin V2 (`docker compose` command)
- **NVIDIA Container Toolkit** (for GPU support)
- **CUDA** 12.x (JetPack 6.2)
- **L4T** 36.4.7 or compatible

> **Verified Configuration**: This service has been tested on Jetson Nano Orin with JetPack 6.2, L4T 36.4.7, CUDA 12.6

## Credits

This service uses pre-built components from:
- **[FastKoko](https://github.com/remsky/Kokoro-FastAPI)** - High-performance FastAPI wrapper for Kokoro TTS
- **[Kokoro TTS](https://github.com/kokoro-onnx/kokoro-onnx)** - High-quality neural text-to-speech engine
- **[jetson-containers](https://github.com/dusty-nv/jetson-containers)** - Pre-built Docker images for NVIDIA Jetson by [@dusty-nv](https://github.com/dusty-nv)
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework

Special thanks to the jetson-containers project for providing optimized, ready-to-use Docker images for Jetson devices!

## License

This project configuration is provided as-is. Please refer to individual component licenses:
- Kokoro TTS license
- jetson-containers license
- NVIDIA software licenses

## Support

For issues and questions:
1. Check logs: `docker compose logs -f`
2. Review interactive API docs: http://localhost:8000/docs
3. Test all endpoints: `./scripts/test.sh`
4. Check service status: `docker ps | grep kokoro`

## Quick Reference

### Common Commands

```bash
# Pull/update image
./scripts/build.sh

# Start service
./scripts/start.sh

# Stop service
./scripts/stop.sh

# View logs
docker compose logs -f

# Generate speech (simple)
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "tts-1", "input": "Hello world", "voice": "alloy", "response_format": "mp3"}' \
  --output output.mp3

# List models
curl http://localhost:8000/v1/models

# List voices
curl http://localhost:8000/v1/audio/voices

# Check service health
curl http://localhost:8000/v1/models

# Run tests
./scripts/test.sh
```

### Service URLs

- **API Base**: http://localhost:8000
- **Web UI**: http://localhost:8000/web
- **API Docs**: http://localhost:8000/docs (Swagger)
- **Models**: http://localhost:8000/v1/models
- **Voices**: http://localhost:8000/v1/audio/voices
