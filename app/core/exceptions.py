import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class EmotionDetectionError(Exception):
    """Raised when emotion inference fails."""
    pass


class AudioSynthesisError(Exception):
    """Raised on TTS synthesis failure."""
    pass


async def emotion_detection_error_handler(request: Request, exc: EmotionDetectionError):
    logger.error(f"EmotionDetectionError: {exc}", exc_info=True)
    return JSONResponse(status_code=502, content={"detail": str(exc)})


async def audio_synthesis_error_handler(request: Request, exc: AudioSynthesisError):
    logger.error(f"AudioSynthesisError: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})

