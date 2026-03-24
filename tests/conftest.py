import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def mock_local_pipeline():
    """Factory fixture: patches get_local_pipeline to return a mock callable."""
    def _mock(emotion="joy", score=0.87):
        emotions = ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"]
        remainder = (1.0 - score) / (len(emotions) - 1)
        result = [
            {"label": e, "score": score if e == emotion else remainder}
            for e in emotions
        ]

        mock_pipeline = MagicMock(return_value=result)
        return patch("app.services.emotion.get_local_pipeline", return_value=mock_pipeline)

    return _mock


@pytest.fixture
def mock_edge_tts():
    """Patches edge_tts.Communicate to return fake MP3 bytes without network calls."""
    import asyncio

    class FakeCommunicate:
        def __init__(self, text="", voice="", rate="", pitch="", volume=""):
            self.text = text

        async def save(self, path):
            with open(path, "wb") as f:
                f.write(b"FAKE_MP3_BYTES")

    return patch("app.services.audio.edge_tts.Communicate", FakeCommunicate)


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)
