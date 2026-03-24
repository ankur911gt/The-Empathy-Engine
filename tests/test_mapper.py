import pytest

from app.services.mapper import get_voice_config, VoiceConfig, _NEUTRAL_BASELINE, _EMOTION_EXTREMES


ALL_EMOTIONS = ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"]


@pytest.mark.parametrize("emotion", ALL_EMOTIONS)
def test_all_emotions_return_valid_config(emotion):
    """All 7 emotions return a valid VoiceConfig."""
    config = get_voice_config(emotion, 0.5)
    assert isinstance(config, VoiceConfig)


def test_neutral_at_zero_intensity():
    """Neutral at intensity=0.0 returns zero modulation."""
    config = get_voice_config("neutral", 0.0)
    assert config.rate == "+0%"
    assert config.pitch == "+0Hz"
    assert config.volume == "+0%"


@pytest.mark.parametrize("emotion", ALL_EMOTIONS)
def test_any_emotion_at_zero_intensity(emotion):
    """Any emotion at intensity=0.0 equals neutral baseline (no modulation)."""
    config = get_voice_config(emotion, 0.0)
    assert config.rate == "+0%"
    assert config.pitch == "+0Hz"
    assert config.volume == "+0%"


@pytest.mark.parametrize("emotion", ALL_EMOTIONS)
def test_any_emotion_at_full_intensity(emotion):
    """Any emotion at intensity=1.0 matches the emotion's extreme values."""
    config = get_voice_config(emotion, 1.0)
    extreme = _EMOTION_EXTREMES[emotion]
    # Parse rate value
    rate_val = int(config.rate.replace("%", "").replace("+", ""))
    assert rate_val == extreme["rate"]


def test_joy_is_fast_and_high():
    """Joy at full intensity has positive rate and pitch."""
    config = get_voice_config("joy", 1.0)
    rate = int(config.rate.replace("%", "").replace("+", ""))
    pitch = int(config.pitch.replace("Hz", "").replace("+", ""))
    assert rate > 0, "Joy should have fast speech rate"
    assert pitch > 0, "Joy should have high pitch"


def test_sadness_is_slow_and_quiet():
    """Sadness at full intensity has negative rate, pitch, and volume."""
    config = get_voice_config("sadness", 1.0)
    rate = int(config.rate.replace("%", "").replace("+", ""))
    pitch = int(config.pitch.replace("Hz", "").replace("+", ""))
    volume = int(config.volume.replace("%", "").replace("+", ""))
    assert rate < 0, "Sadness should have slow speech rate"
    assert pitch < 0, "Sadness should have low pitch"
    assert volume < 0, "Sadness should have quiet volume"


def test_anger_is_loud():
    """Anger at full intensity has high volume."""
    config = get_voice_config("anger", 1.0)
    volume = int(config.volume.replace("%", "").replace("+", ""))
    assert volume > 0, "Anger should have loud volume"


def test_unknown_emotion_returns_neutral():
    """Unknown emotion input returns neutral baseline."""
    config = get_voice_config("unknown_emotion", 0.5)
    neutral_config = get_voice_config("neutral", 0.5)
    assert config.rate == neutral_config.rate
    assert config.pitch == neutral_config.pitch
    assert config.volume == neutral_config.volume


def test_midpoint_interpolation():
    """At intensity=0.5, values are halfway between neutral and extreme."""
    config = get_voice_config("joy", 0.5)
    extreme = _EMOTION_EXTREMES["joy"]
    expected_rate = round(0 + 0.5 * (extreme["rate"] - 0))
    rate_val = int(config.rate.replace("%", "").replace("+", ""))
    assert rate_val == expected_rate


def test_single_voice_for_all_emotions():
    """All emotions use the same voice (AriaNeural)."""
    for emotion in ALL_EMOTIONS:
        config = get_voice_config(emotion, 0.8)
        assert "AriaNeural" in config.voice, f"{emotion} should use AriaNeural"
