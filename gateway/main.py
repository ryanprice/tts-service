"""
TTS Gateway Service with Whisper Alignment

Proxies TTS requests to Kokoro and adds word-level alignment via faster-whisper.
"""

import base64
import io
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TTS_BACKEND_URL = os.getenv("TTS_BACKEND_URL", "http://kokoro-tts:8880")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")

# Global whisper model (lazy loaded)
whisper_model = None


def get_whisper_model():
    """Lazy load whisper model on first use."""
    global whisper_model
    if whisper_model is None:
        logger.info(f"Loading faster-whisper model '{WHISPER_MODEL}' on {WHISPER_DEVICE}...")
        from faster_whisper import WhisperModel
        whisper_model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type="int8" if WHISPER_DEVICE == "cpu" else "float16"
        )
        logger.info("Whisper model loaded successfully")
    return whisper_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info(f"TTS Gateway starting - backend: {TTS_BACKEND_URL}")
    yield
    logger.info("TTS Gateway shutting down")


app = FastAPI(
    title="TTS Gateway with Whisper Alignment",
    description="Proxies Kokoro TTS and adds word-level alignment",
    version="1.0.0",
    lifespan=lifespan
)


# === Request/Response Models ===

class SpeechRequest(BaseModel):
    model: str = "tts-1"
    input: str
    voice: str = "af_alloy"
    response_format: str = "mp3"
    speed: float = 1.0


class AlignRequest(BaseModel):
    audio_file: str = Field(..., description="Base64 encoded audio file")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en'). Auto-detected if not provided.")


class WordTiming(BaseModel):
    word: str
    start: float
    end: float


class AlignResponse(BaseModel):
    words: list[WordTiming]


class SpeechWithAlignmentRequest(BaseModel):
    model: str = "tts-1"
    input: str
    voice: str = "af_alloy"
    response_format: str = "mp3"
    speed: float = 1.0
    language: Optional[str] = Field(None, description="Language code for alignment")


class SpeechWithAlignmentResponse(BaseModel):
    audio: str = Field(..., description="Base64 encoded audio")
    words: list[WordTiming]
    format: str


# === Helper Functions ===

async def proxy_to_tts(path: str, method: str = "GET", json_data: dict = None, follow_redirects: bool = False) -> httpx.Response:
    """Proxy request to TTS backend."""
    url = f"{TTS_BACKEND_URL}{path}"
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=follow_redirects) as client:
        if method == "GET":
            return await client.get(url)
        elif method == "POST":
            return await client.post(url, json=json_data)
        else:
            raise ValueError(f"Unsupported method: {method}")


def transcribe_with_word_timestamps(audio_bytes: bytes, language: str = None) -> list[WordTiming]:
    """Transcribe audio and return word-level timestamps."""
    model = get_whisper_model()

    # Write audio to temp file (faster-whisper needs file path)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    try:
        # Transcribe with word timestamps
        segments, info = model.transcribe(
            temp_path,
            word_timestamps=True,
            language=language,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=200)
        )

        words = []
        for segment in segments:
            if segment.words:
                for word in segment.words:
                    words.append(WordTiming(
                        word=word.word.strip(),
                        start=round(word.start, 3),
                        end=round(word.end, 3)
                    ))

        return words
    finally:
        os.unlink(temp_path)


# === Endpoints ===

@app.get("/")
async def root():
    """Health check and service info."""
    return {
        "service": "TTS Gateway with Whisper Alignment",
        "version": "1.0.0",
        "tts_backend": TTS_BACKEND_URL,
        "whisper_model": WHISPER_MODEL,
        "whisper_device": WHISPER_DEVICE
    }


@app.get("/v1/models")
async def list_models():
    """Proxy to TTS backend - list models."""
    try:
        response = await proxy_to_tts("/v1/models")
        return Response(
            content=response.content,
            status_code=response.status_code,
            media_type="application/json"
        )
    except httpx.RequestError as e:
        logger.error(f"TTS backend error: {e}")
        raise HTTPException(status_code=503, detail="TTS service unavailable")


@app.get("/v1/audio/voices")
async def list_voices():
    """Proxy to TTS backend - list voices."""
    try:
        response = await proxy_to_tts("/v1/audio/voices")
        return Response(
            content=response.content,
            status_code=response.status_code,
            media_type="application/json"
        )
    except httpx.RequestError as e:
        logger.error(f"TTS backend error: {e}")
        raise HTTPException(status_code=503, detail="TTS service unavailable")


@app.post("/v1/audio/speech")
async def generate_speech(request: SpeechRequest):
    """Proxy to TTS backend - generate speech."""
    try:
        response = await proxy_to_tts(
            "/v1/audio/speech",
            method="POST",
            json_data=request.model_dump()
        )

        if response.status_code != 200:
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type="application/json"
            )

        # Determine content type based on format
        content_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "opus": "audio/opus",
            "flac": "audio/flac"
        }
        content_type = content_types.get(request.response_format, "audio/mpeg")

        return Response(
            content=response.content,
            status_code=200,
            media_type=content_type
        )
    except httpx.RequestError as e:
        logger.error(f"TTS backend error: {e}")
        raise HTTPException(status_code=503, detail="TTS service unavailable")


@app.post("/v1/audio/align", response_model=AlignResponse)
async def align_audio(request: AlignRequest):
    """
    Align audio and return word-level timestamps.

    Takes base64 encoded audio and returns word timing information using Whisper.
    """
    try:
        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(request.audio_file)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 encoding: {e}")

        if len(audio_bytes) < 100:
            raise HTTPException(status_code=400, detail="Audio file too small")

        # Transcribe with word timestamps
        logger.info(f"Aligning audio ({len(audio_bytes)} bytes)")
        words = transcribe_with_word_timestamps(audio_bytes, request.language)
        logger.info(f"Found {len(words)} words")

        return AlignResponse(words=words)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Alignment failed")
        raise HTTPException(status_code=500, detail=f"Alignment failed: {e}")


@app.post("/v1/audio/speech_with_alignment", response_model=SpeechWithAlignmentResponse)
async def generate_speech_with_alignment(request: SpeechWithAlignmentRequest):
    """
    Generate speech and return both audio and word-level alignment.

    This is a combined endpoint that:
    1. Generates speech using Kokoro TTS
    2. Runs Whisper alignment on the generated audio
    3. Returns both the audio (base64) and word timestamps
    """
    try:
        # Step 1: Generate TTS audio
        logger.info(f"Generating TTS for: {request.input[:50]}...")
        tts_response = await proxy_to_tts(
            "/v1/audio/speech",
            method="POST",
            json_data={
                "model": request.model,
                "input": request.input,
                "voice": request.voice,
                "response_format": request.response_format,
                "speed": request.speed
            }
        )

        if tts_response.status_code != 200:
            raise HTTPException(
                status_code=tts_response.status_code,
                detail=f"TTS generation failed: {tts_response.text}"
            )

        audio_bytes = tts_response.content
        logger.info(f"TTS generated {len(audio_bytes)} bytes")

        # Step 2: Align the generated audio
        logger.info("Running Whisper alignment...")

        # Detect language from input if not provided
        language = request.language
        if not language:
            # Simple heuristic - could be improved
            if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in request.input):
                language = "ja"
            elif any('\u4e00' <= c <= '\u9fff' for c in request.input):
                language = "zh"
            else:
                language = "en"

        words = transcribe_with_word_timestamps(audio_bytes, language)
        logger.info(f"Alignment found {len(words)} words")

        # Step 3: Return combined response
        return SpeechWithAlignmentResponse(
            audio=base64.b64encode(audio_bytes).decode("utf-8"),
            words=words,
            format=request.response_format
        )

    except HTTPException:
        raise
    except httpx.RequestError as e:
        logger.error(f"TTS backend error: {e}")
        raise HTTPException(status_code=503, detail="TTS service unavailable")
    except Exception as e:
        logger.exception("Speech with alignment failed")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


# === Web UI Proxy ===

@app.get("/web")
@app.get("/web/")
@app.get("/web/{path:path}")
async def proxy_web(path: str = ""):
    """Proxy web UI requests to TTS backend."""
    try:
        # Always include trailing slash to match backend's expected format
        web_path = f"/web/{path}" if path else "/web/"
        response = await proxy_to_tts(web_path, follow_redirects=True)
        return Response(
            content=response.content,
            status_code=response.status_code,
            media_type=response.headers.get("content-type", "text/html")
        )
    except httpx.RequestError as e:
        logger.error(f"Web proxy error: {e}")
        raise HTTPException(status_code=503, detail="TTS service unavailable")


@app.get("/docs")
async def docs_redirect():
    """Redirect to FastAPI auto-generated docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
