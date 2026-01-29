# TTS Gateway with Whisper Alignment
# Runs faster-whisper on CPU for word-level alignment

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create cache directory for whisper models
RUN mkdir -p /root/.cache/huggingface

# Environment defaults
ENV TTS_BACKEND_URL=http://kokoro-tts:8880
ENV WHISPER_MODEL=tiny
ENV WHISPER_DEVICE=cpu
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
