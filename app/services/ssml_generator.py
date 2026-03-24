"""
SSML (Speech Synthesis Markup Language) generator for enhanced prosody control.

Generates SSML markup with:
- <break> tags for emotional pauses
- <prosody> tags for per-sentence rate/pitch/volume variation  
- <emphasis> for stress words
- Emotion-specific timing patterns

This module generates SSML that edge-tts can process via Microsoft's neural speech service.
"""

import re
from app.services.mapper import VoiceConfig


def generate_ssml(
    processed_text: str,
    voice_config: VoiceConfig,
    emotion: str,
    intensity: float,
) -> str:
    """Generate full SSML document for the given text and voice configuration.
    
    Returns a complete <speak> document with per-sentence prosody and emotional pauses.
    """
    sentences = _split_sentences(processed_text)
    
    body_parts = []
    
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Add inter-sentence break based on emotion
        if i > 0:
            break_ms = _get_inter_sentence_break(emotion, intensity)
            body_parts.append(f'        <break time="{break_ms}ms"/>')
        
        # Apply per-sentence prosody variation
        rate, pitch, volume = _get_sentence_prosody(voice_config, emotion, i, len(sentences))
        
        # Mark stress words with emphasis
        marked_sentence = _apply_emphasis(sentence, emotion, intensity)
        
        body_parts.append(
            f'        <prosody rate="{rate}" pitch="{pitch}" volume="{volume}">'
            f'{marked_sentence}</prosody>'
        )
    
    body = "\n".join(body_parts)
    
    ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <voice name="{voice_config.voice}">
{body}
    </voice>
</speak>"""
    
    return ssml


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    parts = re.split(r'(?<=[.!?…])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def _get_inter_sentence_break(emotion: str, intensity: float) -> int:
    """Get pause duration (ms) between sentences based on emotion.
    
    - Sadness: long pauses (heavy, weary delivery)
    - Anger: short pauses (rapid-fire, aggressive)
    - Fear: medium-long pauses (hesitant, uncertain)
    - Joy: short pauses (energetic flow)
    - Surprise: very short (breathless)
    - Disgust: medium pauses (measured, deliberate)
    """
    base_breaks = {
        "sadness":  600,
        "anger":    200,
        "fear":     500,
        "joy":      250,
        "surprise": 200,
        "disgust":  400,
        "neutral":  350,
    }
    base = base_breaks.get(emotion, 350)
    # Scale with intensity
    return int(base * (0.5 + intensity * 0.5))


def _get_sentence_prosody(
    voice_config: VoiceConfig, emotion: str, index: int, total: int
) -> tuple[str, str, str]:
    """Get per-sentence prosody with natural variation.
    
    Returns (rate, pitch, volume) strings for SSML prosody tag.
    """
    base_rate = int(voice_config.rate.replace("%", "").replace("+", ""))
    base_pitch = int(voice_config.pitch.replace("Hz", "").replace("+", ""))
    base_volume = int(voice_config.volume.replace("%", "").replace("+", ""))
    
    # Add variation per sentence position
    # First sentence: slightly more intense (hook)
    # Middle: baseline
    # Last sentence: context-dependent (anger=punchy, sadness=trailing)
    if total > 1:
        progress = index / max(total - 1, 1)
        
        if emotion in ("sadness", "fear"):
            # Gradually slow down and get quieter
            rate_adj = -int(progress * 8)
            volume_adj = -int(progress * 5)
            pitch_adj = -int(progress * 3)
        elif emotion in ("anger",):
            # Stay intense, slight crescendo
            rate_adj = int(progress * 3)
            volume_adj = int(progress * 5)
            pitch_adj = 0
        elif emotion in ("joy", "surprise"):
            # Stay upbeat, slight variation
            rate_adj = -int(progress * 3) if index % 2 == 0 else int(progress * 2)
            volume_adj = 0
            pitch_adj = int(progress * 2)
        else:
            rate_adj = 0
            volume_adj = 0
            pitch_adj = 0
    else:
        rate_adj = 0
        volume_adj = 0
        pitch_adj = 0
    
    rate = base_rate + rate_adj
    pitch = base_pitch + pitch_adj
    volume = base_volume + volume_adj
    
    return (
        f"{'+' if rate >= 0 else ''}{rate}%",
        f"{'+' if pitch >= 0 else ''}{pitch}Hz",
        f"{'+' if volume >= 0 else ''}{volume}%",
    )


def _apply_emphasis(sentence: str, emotion: str, intensity: float) -> str:
    """Add SSML emphasis tags to stress words.
    
    Only applies at higher intensities to avoid over-marking.
    """
    if intensity < 0.5:
        return _escape_xml(sentence)
    
    text = _escape_xml(sentence)
    
    # Mark ALL-CAPS words with strong emphasis
    text = re.sub(
        r'\b([A-Z]{2,})\b',
        r'<emphasis level="strong">\1</emphasis>',
        text,
    )
    
    return text


def _escape_xml(text: str) -> str:
    """Escape XML special characters."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text
