from dataclasses import dataclass


@dataclass
class VoiceConfig:
    """Voice configuration for edge-tts with rate, pitch, and volume control."""
    rate: str       # e.g. "+20%", "-30%", "+0%"
    pitch: str      # e.g. "+10Hz", "-15Hz", "+0Hz"
    volume: str     # e.g. "+10%", "-20%", "+0%"
    voice: str      # Microsoft voice name


# Single voice for all emotions — AriaNeural is the most expressive edge-tts voice.
# The assignment requires modulating parameters (rate, pitch, volume) of ONE voice,
# not switching between different speakers.
DEFAULT_VOICE = "en-US-AriaNeural"

# Neutral baseline (no modulation)
_NEUTRAL_BASELINE = {"rate": 0, "pitch": 0, "volume": 0}

# =============================================================================
# EMOTION EXTREMES — at intensity=1.0
#
# These are pushed to near-maximum safe values for edge-tts to make emotions
# CLEARLY audible. The differences at full intensity should be dramatic.
#
# Psychology model:
#   - High arousal emotions (joy, anger, fear, surprise) → fast rate, ±pitch, loud
#   - Low arousal emotions (sadness, disgust) → slow rate, low pitch, quiet
#   - Valence determines pitch direction: positive=high, negative=low
#
# Edge-tts safe ranges: rate ±50%, pitch ±50Hz, volume ±50%
# =============================================================================
_EMOTION_EXTREMES = {
    # JOY: Fast, high-pitched, loud — excited and energetic
    "joy":      {"rate": 35,  "pitch": 30,  "volume": 15},

    # SADNESS: Very slow, low-pitched, quiet — heavy and dragging
    "sadness":  {"rate": -40, "pitch": -25, "volume": -25},

    # ANGER: Fast, deep-pitched, VERY loud — intense and forceful
    "anger":    {"rate": 25,  "pitch": -15, "volume": 30},

    # FEAR: Fast, high-pitched, quiet — breathless and panicked
    "fear":     {"rate": 30,  "pitch": 25,  "volume": -15},

    # DISGUST: Slow, low-pitched, quiet — dismissive and flat
    "disgust":  {"rate": -25, "pitch": -18, "volume": -10},

    # SURPRISE: Fast, VERY high-pitched, loud — startled and emphatic
    "surprise": {"rate": 20,  "pitch": 40,  "volume": 20},

    # NEUTRAL: No change at all
    "neutral":  {"rate": 0,   "pitch": 0,   "volume": 0},
}


def _interpolate(neutral_val: float, extreme_val: float, intensity: float) -> float:
    """Linear interpolation between neutral and extreme based on intensity."""
    return neutral_val + intensity * (extreme_val - neutral_val)


def get_voice_config(emotion: str, intensity: float) -> VoiceConfig:
    """Map (emotion, intensity) → edge-tts voice parameters via linear interpolation.
    
    At intensity=0.0 → neutral baseline (no modulation)
    At intensity=1.0 → full emotion extremes
    Everything in between is linearly interpolated.
    """
    extreme = _EMOTION_EXTREMES.get(emotion, _EMOTION_EXTREMES["neutral"])
    neutral = _NEUTRAL_BASELINE

    rate = round(_interpolate(neutral["rate"], extreme["rate"], intensity))
    pitch = round(_interpolate(neutral["pitch"], extreme["pitch"], intensity))
    volume = round(_interpolate(neutral["volume"], extreme["volume"], intensity))

    return VoiceConfig(
        rate=f"{'+' if rate >= 0 else ''}{rate}%",
        pitch=f"{'+' if pitch >= 0 else ''}{pitch}Hz",
        volume=f"{'+' if volume >= 0 else ''}{volume}%",
        voice=DEFAULT_VOICE,
    )
