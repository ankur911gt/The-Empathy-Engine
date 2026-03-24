import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


client = TestClient(app)


class TestAnalyzeEndpoint:
    def test_valid_text_returns_200(self, mock_local_pipeline, mock_edge_tts):
        """POST /api/analyze with valid text returns 200 with all fields."""
        with mock_local_pipeline("joy", 0.87), mock_edge_tts:
            response = client.post("/api/analyze", json={"text": "I am so happy today!"})

        assert response.status_code == 200
        data = response.json()
        assert "emotion" in data
        assert "intensity" in data
        assert "all_scores" in data
        assert "detection_source" in data
        assert "voice_params" in data
        assert "original_text" in data
        assert "processed_text" in data
        assert "ssml_text" in data
        assert "audio_url" in data
        assert "processing_time_ms" in data
        assert data["audio_url"].startswith("/api/audio/")

    def test_forced_emotion_mode(self, mock_local_pipeline, mock_edge_tts):
        """POST /api/analyze with forced emotion skips detection."""
        with mock_local_pipeline("neutral", 0.5), mock_edge_tts:
            response = client.post("/api/analyze", json={"text": "Hello world", "emotion": "anger"})

        assert response.status_code == 200
        data = response.json()
        assert data["emotion"] == "anger"
        assert data["detection_source"] == "forced"

    def test_empty_string_returns_422(self):
        """POST /api/analyze with empty text returns 422."""
        response = client.post("/api/analyze", json={"text": ""})
        assert response.status_code == 422

    def test_text_over_2000_returns_422(self):
        """POST /api/analyze with text over 2000 chars returns 422."""
        response = client.post("/api/analyze", json={"text": "x" * 2001})
        assert response.status_code == 422

    def test_response_contains_ssml(self, mock_local_pipeline, mock_edge_tts):
        """Response includes SSML markup with speak and prosody tags."""
        with mock_local_pipeline("sadness", 0.9), mock_edge_tts:
            response = client.post("/api/analyze", json={"text": "I miss everything."})

        data = response.json()
        assert "<speak" in data["ssml_text"]
        assert "<prosody" in data["ssml_text"]
        assert "AriaNeural" in data["ssml_text"]


class TestAudioEndpoint:
    def test_valid_file_returns_200(self):
        """GET /api/audio/{valid_32hex}.mp3 returns 200 when file exists."""
        filename = "a" * 32 + ".mp3"
        output_dir = Path(settings.audio_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename
        filepath.write_bytes(b"fake mp3 data")

        try:
            response = client.get(f"/api/audio/{filename}")
            assert response.status_code == 200
        finally:
            filepath.unlink(missing_ok=True)

    def test_nonexistent_file_returns_404(self):
        """GET /api/audio/nonexistent.mp3 returns 404."""
        filename = "b" * 32 + ".mp3"
        response = client.get(f"/api/audio/{filename}")
        assert response.status_code == 404

    def test_path_traversal_blocked(self):
        """GET /api/audio/../../etc/passwd is blocked (returns 4xx)."""
        response = client.get("/api/audio/../../etc/passwd")
        assert response.status_code in (400, 404)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        """GET /api/health returns 200 with status ok."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "hf_model_loaded" in data


class TestCache:
    def test_cache_prevents_duplicate_tts_calls(self, mock_local_pipeline, mock_edge_tts):
        """Submit identical text twice — second should be cache hit."""
        from app.core.cache import _cache
        _cache.clear()

        with mock_local_pipeline("joy", 0.87), mock_edge_tts:
            r1 = client.post("/api/analyze", json={"text": "Cache test text"})
            assert r1.status_code == 200

            r2 = client.post("/api/analyze", json={"text": "Cache test text"})
            assert r2.status_code == 200

        # Both should return the same audio URL
        assert r1.json()["audio_url"] == r2.json()["audio_url"]
