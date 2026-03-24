import io
import logging
import random
import re
import uuid
from pathlib import Path

import edge_tts

from app.core.config import settings
from app.core.exceptions import AudioSynthesisError
from app.services.mapper import VoiceConfig

logger = logging.getLogger(__name__)


def _sanitize_text(text: str) -> str:
    """Clean text of characters that can cause edge-tts to fail."""
    text = text.replace("—", ", ").replace("–", ", ")
    text = re.sub(r"\.{4,}", "...", text)
    text = re.sub(r"[^\w\s.,!?;:'\"-…]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        text = "No text provided."
    return text


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences for per-sentence synthesis."""
    # Split on sentence-ending punctuation followed by space or end
    parts = re.split(r'(?<=[.!?…])\s+', text)
    # Also split on ellipsis
    result = []
    for part in parts:
        if part.strip():
            result.append(part.strip())
    return result if result else [text]


def _vary_params(voice_config: VoiceConfig, sentence_index: int, total_sentences: int) -> VoiceConfig:
    """Add subtle natural variation to voice params per sentence.
    
    Humans don't speak every sentence at the same speed/pitch.
    This adds ±3-5% random variation to make it sound more natural.
    """
    base_rate = int(voice_config.rate.replace("%", "").replace("+", ""))
    base_pitch = int(voice_config.pitch.replace("Hz", "").replace("+", ""))
    base_volume = int(voice_config.volume.replace("%", "").replace("+", ""))

    # Add small random variation
    rate_var = random.randint(-3, 3)
    pitch_var = random.randint(-2, 2)
    vol_var = random.randint(-2, 2)

    # Gradually slow down towards the end of longer texts (natural human pattern)
    if total_sentences > 2:
        progress = sentence_index / max(total_sentences - 1, 1)
        # Last sentences are slightly slower
        rate_var -= int(progress * 4)

    new_rate = base_rate + rate_var
    new_pitch = base_pitch + pitch_var
    new_volume = base_volume + vol_var

    return VoiceConfig(
        rate=f"{'+' if new_rate >= 0 else ''}{new_rate}%",
        pitch=f"{'+' if new_pitch >= 0 else ''}{new_pitch}Hz",
        volume=f"{'+' if new_volume >= 0 else ''}{new_volume}%",
        voice=voice_config.voice,
    )


async def synthesize_speech(
    processed_text: str, voice_config: VoiceConfig
) -> tuple[bytes, str]:
    """Synthesize speech via edge-tts with sentence-by-sentence variation."""

    sanitized_text = _sanitize_text(processed_text)
    sentences = _split_into_sentences(sanitized_text)

    logger.info(
        f"Synthesizing {len(sentences)} sentence(s): voice={voice_config.voice} "
        f"rate={voice_config.rate} pitch={voice_config.pitch} vol={voice_config.volume}"
    )

    if len(sentences) <= 1:
        # Single sentence — synthesize directly
        audio_bytes, _ = await _synth_with_retry(sanitized_text, voice_config)
        # Save to disk so the /audio endpoint can serve it
        filename = f"{uuid.uuid4().hex}.mp3"
        output_dir = Path(settings.audio_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / filename).write_bytes(audio_bytes)
        logger.info(f"Audio synthesized: {filename} (single sentence)")
        return audio_bytes, filename

    # Multi-sentence: synthesize each with slight variation, then concatenate
    all_audio_bytes = []

    for idx, sentence in enumerate(sentences):
        varied_config = _vary_params(voice_config, idx, len(sentences))

        try:
            audio_bytes, _ = await _synth_single(sentence, varied_config)
            all_audio_bytes.append(audio_bytes)
        except Exception as e:
            logger.warning(f"Sentence {idx} failed with varied params, retrying with base: {e}")
            try:
                audio_bytes, _ = await _synth_single(sentence, voice_config)
                all_audio_bytes.append(audio_bytes)
            except Exception as e2:
                logger.warning(f"Sentence {idx} failed with base params too, using default: {e2}")
                default = VoiceConfig(rate="+0%", pitch="+0Hz", volume="+0%", voice="en-US-AriaNeural")
                audio_bytes, _ = await _synth_single(sentence, default)
                all_audio_bytes.append(audio_bytes)

    # Concatenate all MP3 segments (MP3 is frame-based, simple concat works)
    combined = b"".join(all_audio_bytes)

    # Save combined audio
    filename = f"{uuid.uuid4().hex}.mp3"
    output_dir = Path(settings.audio_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_bytes(combined)

    logger.info(f"Audio synthesized: {filename} ({len(sentences)} segments combined)")

    return combined, filename


async def _synth_with_retry(text: str, voice_config: VoiceConfig) -> tuple[bytes, str]:
    """Synthesize with retry on failure using default params."""
    try:
        return await _synth_single(text, voice_config)
    except Exception as e:
        logger.warning(f"Synthesis failed ({e}), retrying with default params...")

    try:
        default = VoiceConfig(rate="+0%", pitch="+0Hz", volume="+0%", voice="en-US-AriaNeural")
        return await _synth_single(text, default)
    except Exception as e:
        raise AudioSynthesisError(f"Edge-TTS synthesis failed: {str(e)}") from e


async def _synth_single(text: str, voice_config: VoiceConfig) -> tuple[bytes, str]:
    """Perform a single edge-tts synthesis call."""
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_config.voice,
        rate=voice_config.rate,
        pitch=voice_config.pitch,
        volume=voice_config.volume,
    )

    filename = f"{uuid.uuid4().hex}.mp3"
    output_dir = Path(settings.audio_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    await communicate.save(str(output_path))
    audio_bytes = output_path.read_bytes()

    # Clean up individual segment files (we'll save the combined one later)
    output_path.unlink(missing_ok=True)

    return audio_bytes, filename
