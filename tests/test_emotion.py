import pytest
from unittest.mock import MagicMock, patch

from app.services.emotion import detect_emotion, VALID_EMOTIONS, _compute_keyword_boosts


@pytest.mark.asyncio
async def test_local_model_returns_valid_result(mock_local_pipeline):
    """Local pipeline returns EmotionResult with correct fields."""
    with mock_local_pipeline("joy", 0.87):
        result = await detect_emotion("I'm so happy!")
    assert result.emotion == "joy"
    assert result.detection_source == "local"
    assert 0.0 <= result.intensity <= 1.0
    assert len(result.all_scores) == 7


@pytest.mark.asyncio
@pytest.mark.parametrize("emotion", list(VALID_EMOTIONS))
async def test_all_seven_emotions(mock_local_pipeline, emotion):
    """All 7 emotions are correctly returned from local pipeline."""
    with mock_local_pipeline(emotion, 0.85):
        result = await detect_emotion(f"Test {emotion}")
    assert result.emotion == emotion
    assert result.emotion in VALID_EMOTIONS


@pytest.mark.asyncio
async def test_unknown_emotion_sanitized(mock_local_pipeline):
    """Unknown emotion label gets replaced with 'neutral'."""
    result_data = [
        {"label": "unknown_emotion", "score": 0.90},
        {"label": "joy", "score": 0.05},
        {"label": "sadness", "score": 0.01},
        {"label": "anger", "score": 0.01},
        {"label": "fear", "score": 0.01},
        {"label": "disgust", "score": 0.01},
        {"label": "surprise", "score": 0.01},
    ]
    mock_pipeline = MagicMock(return_value=result_data)

    with patch("app.services.emotion.get_local_pipeline", return_value=mock_pipeline):
        result = await detect_emotion("Test unknown")
    assert result.emotion == "neutral"


# ========================================================================
# Keyword boosting tests
# ========================================================================

def test_anger_keywords_detected():
    """Anger keywords produce boost."""
    boosts = _compute_keyword_boosts("I NEVER want to see you again, you ruined everything!")
    assert "anger" in boosts
    assert boosts["anger"] > 0


def test_joy_keywords_detected():
    """Joy keywords produce boost."""
    boosts = _compute_keyword_boosts("This is the most amazing wonderful day of my life!")
    assert "joy" in boosts
    assert boosts["joy"] > 0


def test_sadness_keywords_detected():
    """Sadness keywords produce boost."""
    boosts = _compute_keyword_boosts("I miss her so much, I feel so empty and lonely.")
    assert "sadness" in boosts
    assert boosts["sadness"] > 0


def test_fear_keywords_detected():
    """Fear keywords produce boost."""
    boosts = _compute_keyword_boosts("I'm terrified, what if something bad happens?")
    assert "fear" in boosts
    assert boosts["fear"] > 0


def test_neutral_text_no_boost():
    """Neutral factual text produces no meaningful boost."""
    boosts = _compute_keyword_boosts("The meeting is scheduled for 3pm today.")
    # Should have no strong boosts
    if boosts:
        assert all(v < 0.1 for v in boosts.values())


@pytest.mark.asyncio
async def test_keyword_boost_overrides_weak_model():
    """When model returns weak neutral but text has strong anger words, boost should fix it."""
    result_data = [
        {"label": "neutral", "score": 0.30},
        {"label": "anger", "score": 0.25},
        {"label": "joy", "score": 0.10},
        {"label": "sadness", "score": 0.10},
        {"label": "fear", "score": 0.10},
        {"label": "disgust", "score": 0.10},
        {"label": "surprise", "score": 0.05},
    ]
    mock_pipeline = MagicMock(return_value=result_data)

    with patch("app.services.emotion.get_local_pipeline", return_value=mock_pipeline):
        result = await detect_emotion("You ruined EVERYTHING, I am furious!")
    assert result.emotion == "anger", "Keyword boost should override weak neutral"
