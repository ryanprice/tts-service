#!/usr/bin/env python3
"""
API tests for TTS Gateway Service
Tests all endpoints including Whisper alignment
"""

import base64
import requests
import json
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_service_available():
    """Test if service is running"""
    print("[1/8] Testing service availability...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "service" in data
        print("✅ Service is available")
        print(f"   Service: {data.get('service')}")
        print(f"   Whisper model: {data.get('whisper_model')}")
        return True
    except Exception as e:
        print(f"❌ Service not available: {e}")
        return False


def test_models_endpoint():
    """Test /v1/models endpoint"""
    print("\n[2/8] Testing /v1/models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "models" in data or "tts-1" in str(data)
        print(f"✅ Models endpoint working")
        print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
        return True
    except Exception as e:
        print(f"❌ Models endpoint failed: {e}")
        return False


def test_voices_endpoint():
    """Test /v1/audio/voices endpoint"""
    print("\n[3/8] Testing /v1/audio/voices endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/v1/audio/voices", timeout=5)
        assert response.status_code == 200
        data = response.json()

        if "voices" in data:
            voices = data["voices"]
            print(f"✅ Voices endpoint working")
            print(f"   Found {len(voices)} voices")
            if voices:
                # Handle both dict and string voice formats
                sample = []
                for v in voices[:3]:
                    if isinstance(v, dict):
                        sample.append(v.get('id', v.get('name', str(v))))
                    else:
                        sample.append(str(v))
                print(f"   Sample voices: {sample}")
        else:
            print(f"✅ Voices endpoint working")
            print(f"   Response format: {list(data.keys())}")

        return True
    except Exception as e:
        print(f"❌ Voices endpoint failed: {e}")
        return False


def test_speech_generation_mp3():
    """Test speech generation with MP3 format"""
    print("\n[4/8] Testing speech generation (MP3)...")
    try:
        payload = {
            "model": "tts-1",
            "input": "This is a test of the Kokoro text to speech service running on Jetson Nano Orin.",
            "voice": "af_alloy",
            "response_format": "mp3"
        }

        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/audio/speech",
            json=payload,
            timeout=30
        )
        end_time = time.time()
        duration = end_time - start_time

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert len(response.content) > 1000, f"Audio too small: {len(response.content)} bytes"

        # Verify it's an MP3 file (check for MP3 header)
        assert response.content[:3] in [b'ID3', b'\xff\xfb', b'\xff\xf3'], "Not a valid MP3 file"

        print(f"✅ MP3 generation successful")
        print(f"   File size: {len(response.content)} bytes")
        print(f"   Generation time: {duration:.2f}s")

        # Save for alignment test
        global test_audio_bytes
        test_audio_bytes = response.content

        return True
    except Exception as e:
        print(f"❌ Speech generation failed: {e}")
        return False


def test_audio_alignment():
    """Test /v1/audio/align endpoint"""
    print("\n[5/8] Testing audio alignment endpoint...")
    try:
        # First generate some audio to align
        tts_payload = {
            "model": "tts-1",
            "input": "Hello world, this is a test.",
            "voice": "af_alloy",
            "response_format": "mp3"
        }

        tts_response = requests.post(
            f"{BASE_URL}/v1/audio/speech",
            json=tts_payload,
            timeout=30
        )
        assert tts_response.status_code == 200, "Failed to generate TTS for alignment test"

        # Now test alignment
        audio_base64 = base64.b64encode(tts_response.content).decode("utf-8")
        align_payload = {
            "audio_file": audio_base64
        }

        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/audio/align",
            json=align_payload,
            timeout=60
        )
        duration = time.time() - start_time

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "words" in data, "Response missing 'words' field"

        words = data["words"]
        print(f"✅ Audio alignment successful")
        print(f"   Found {len(words)} words")
        print(f"   Alignment time: {duration:.2f}s")
        if words:
            print(f"   Sample: {words[:3]}")

        return True
    except Exception as e:
        print(f"❌ Audio alignment failed: {e}")
        return False


def test_speech_with_alignment():
    """Test /v1/audio/speech_with_alignment combined endpoint"""
    print("\n[6/8] Testing combined speech + alignment endpoint...")
    try:
        payload = {
            "model": "tts-1",
            "input": "The quick brown fox jumps over the lazy dog.",
            "voice": "af_alloy",
            "response_format": "mp3"
        }

        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/audio/speech_with_alignment",
            json=payload,
            timeout=90
        )
        duration = time.time() - start_time

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert "audio" in data, "Response missing 'audio' field"
        assert "words" in data, "Response missing 'words' field"
        assert "format" in data, "Response missing 'format' field"

        # Verify audio can be decoded
        audio_bytes = base64.b64decode(data["audio"])
        assert len(audio_bytes) > 1000, f"Audio too small: {len(audio_bytes)} bytes"

        words = data["words"]
        print(f"✅ Combined speech + alignment successful")
        print(f"   Audio size: {len(audio_bytes)} bytes")
        print(f"   Found {len(words)} words")
        print(f"   Total time: {duration:.2f}s")
        if words:
            print(f"   Word timings: {words[:5]}")

        return True
    except Exception as e:
        print(f"❌ Combined speech + alignment failed: {e}")
        return False


def test_voice_selection():
    """Test different voice selection"""
    print("\n[7/8] Testing voice selection...")
    try:
        voices_to_test = ["af_alloy", "af_bella", "af_nova"]
        results = []

        for voice in voices_to_test:
            payload = {
                "model": "tts-1",
                "input": "Testing voice.",
                "voice": voice,
                "response_format": "mp3"
            }

            response = requests.post(
                f"{BASE_URL}/v1/audio/speech",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                results.append(f"{voice}: {len(response.content)} bytes")
            else:
                results.append(f"{voice}: not available (HTTP {response.status_code})")

        print(f"✅ Voice selection tested")
        for result in results:
            print(f"   {result}")

        return True
    except Exception as e:
        print(f"❌ Voice selection test failed: {e}")
        return False


def test_error_handling():
    """Test error handling with invalid requests"""
    print("\n[8/8] Testing error handling...")
    try:
        # Test with missing required fields
        payload = {
            "model": "tts-1"
            # Missing 'input' field
        }

        response = requests.post(
            f"{BASE_URL}/v1/audio/speech",
            json=payload,
            timeout=10
        )

        # Should return 4xx error
        assert response.status_code >= 400 and response.status_code < 500, \
            f"Expected 4xx error, got {response.status_code}"

        # Test invalid base64 for alignment
        response = requests.post(
            f"{BASE_URL}/v1/audio/align",
            json={"audio_file": "not-valid-base64!!!"},
            timeout=10
        )
        assert response.status_code >= 400, f"Expected error for invalid base64, got {response.status_code}"

        print(f"✅ Error handling working")
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("TTS Gateway Service API Tests")
    print("(with Whisper Alignment)")
    print("=" * 50)
    print()

    tests = [
        test_service_available,
        test_models_endpoint,
        test_voices_endpoint,
        test_speech_generation_mp3,
        test_audio_alignment,
        test_speech_with_alignment,
        test_voice_selection,
        test_error_handling,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 50)

    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
