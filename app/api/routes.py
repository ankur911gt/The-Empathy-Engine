import logging
import re
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse, VoiceParams
from app.core.cache import get_cached, make_cache_key, set_cached
from app.core.config import settings
from app.services.audio import synthesize_speech
from app.services.emotion import detect_emotion, EmotionResult, VALID_EMOTIONS
from app.services.mapper import get_voice_config
from app.services.text_preprocessor import preprocess_text
from app.services.ssml_generator import generate_ssml

logger = logging.getLogger(__name__)

router = APIRouter()

# Regex for valid audio filenames: 32 hex chars + .mp3
_FILENAME_RE = re.compile(r"^[a-f0-9]{32}\.mp3$")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """Full pipeline: emotion detection → voice mapping → text enrichment → SSML → TTS."""
    start_time = time.time()
    text = request.text

    # Step 1: Detect emotion (or use forced emotion for comparison mode)
    if request.emotion and request.emotion in VALID_EMOTIONS:
        forced_emotion = request.emotion
        emotion_result = EmotionResult(
            emotion=forced_emotion,
            intensity=0.85,
            all_scores={e: (0.85 if e == forced_emotion else 0.02) for e in VALID_EMOTIONS},
            detection_source="forced",
        )
        logger.info(f"Forced emotion mode: {forced_emotion}")
    else:
        emotion_result = await detect_emotion(text)

    # Step 2: Check cache
    cache_key = make_cache_key(text, emotion_result.emotion, emotion_result.intensity)
    cached = get_cached(cache_key)

    if cached:
        audio_bytes, filename = cached
        filepath = Path(settings.audio_output_dir) / filename
        if not filepath.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_bytes(audio_bytes)
        logger.info(f"Cache hit for key {cache_key[:12]}...")
    else:
        # Step 3: Get voice config
        voice_config = get_voice_config(emotion_result.emotion, emotion_result.intensity)

        # Step 4: Preprocess text with emotion-specific enrichment
        processed_text = preprocess_text(text, emotion_result.emotion, emotion_result.intensity)

        # Step 5: Synthesize speech
        audio_bytes, filename = await synthesize_speech(processed_text, voice_config)

        # Step 6: Cache
        set_cached(cache_key, audio_bytes, filename)

    # Build response data
    voice_config = get_voice_config(emotion_result.emotion, emotion_result.intensity)
    processed_text = preprocess_text(text, emotion_result.emotion, emotion_result.intensity)

    # Step 7: Generate SSML representation
    ssml_text = generate_ssml(processed_text, voice_config, emotion_result.emotion, emotion_result.intensity)

    return AnalyzeResponse(
        emotion=emotion_result.emotion,
        intensity=round(emotion_result.intensity, 4),
        all_scores={k: round(v, 4) for k, v in emotion_result.all_scores.items()},
        detection_source=emotion_result.detection_source,
        voice_params=VoiceParams(
            rate=voice_config.rate,
            pitch=voice_config.pitch,
            volume=voice_config.volume,
            voice=voice_config.voice,
        ),
        original_text=text,
        processed_text=processed_text,
        ssml_text=ssml_text,
        audio_url=f"/api/audio/{filename}",
        processing_time_ms=round((time.time() - start_time) * 1000, 1),
    )


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve a generated audio file."""
    if not _FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename format")

    filepath = Path(settings.audio_output_dir) / filename

    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(str(filepath), media_type="audio/mpeg")


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    from app.core import local_model

    return HealthResponse(
        status="ok",
        hf_model_loaded=local_model._pipeline is not None,
    )
