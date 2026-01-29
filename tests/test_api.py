#!/usr/bin/env python3
"""
API tests for Kokoro TTS Service
Tests all endpoints and validates responses
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_service_available():
    """Test if service is running"""
    print("[1/6] Testing service availability...")
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✅ Service is available")
        return True
    except Exception as e:
        print(f"❌ Service not available: {e}")
        return False


def test_models_endpoint():
    """Test /v1/models endpoint"""
    print("\n[2/6] Testing /v1/models endpoint...")
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
    print("\n[3/6] Testing /v1/audio/voices endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/v1/audio/voices", timeout=5)
        assert response.status_code == 200
        data = response.json()

        # Check if voices are returned
        if "voices" in data:
            voices = data["voices"]
            print(f"✅ Voices endpoint working")
            print(f"   Found {len(voices)} voices")
            if voices:
                print(f"   Sample voices: {[v.get('id', v.get('name', str(v))) for v in voices[:3]]}")
        else:
            print(f"✅ Voices endpoint working")
            print(f"   Response format: {list(data.keys())}")

        return True
    except Exception as e:
        print(f"❌ Voices endpoint failed: {e}")
        return False


def test_speech_generation_mp3():
    """Test speech generation with MP3 format"""
    print("\n[4/6] Testing speech generation (MP3)...")
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

        # Calculate approximate RTF
        # Assuming ~150 words/min speaking rate
        word_count = len(payload["input"].split())
        estimated_duration = (word_count / 150) * 60  # seconds
        if estimated_duration > 0:
            rtf = duration / estimated_duration
            print(f"   Estimated RTF: {rtf:.2f} (target: <1.0)")

        return True
    except Exception as e:
        print(f"❌ Speech generation failed: {e}")
        return False


def test_voice_selection():
    """Test different voice selection"""
    print("\n[5/6] Testing voice selection...")
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
                # Voice might not be available
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
    print("\n[6/6] Testing error handling...")
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

        print(f"✅ Error handling working (HTTP {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("Kokoro TTS Service API Tests")
    print("=" * 50)
    print()

    tests = [
        test_service_available,
        test_models_endpoint,
        test_voices_endpoint,
        test_speech_generation_mp3,
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
