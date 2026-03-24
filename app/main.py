import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.exceptions import (
    AudioSynthesisError,
    EmotionDetectionError,
    audio_synthesis_error_handler,
    emotion_detection_error_handler,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan hook — startup and shutdown."""
    # Startup
    Path(settings.audio_output_dir).mkdir(parents=True, exist_ok=True)
    logger.info("Empathy Engine starting up")
    logger.info(
        f"HF Inference API: "
        f"{'configured' if settings.hf_api_token else 'NOT configured — set HF_API_TOKEN'}"
    )
    logger.info(
        f"ElevenLabs: "
        f"{'configured' if settings.elevenlabs_api_key else 'NOT configured — set ELEVENLABS_API_KEY'}"
    )
    logger.info(f"Audio output directory: {settings.audio_output_dir}")
    # Do NOT pre-load the local model
    yield
    # Shutdown (nothing to clean up)


app = FastAPI(
    title="The Empathy Engine",
    description="Dynamically modulates vocal characteristics of synthesized speech based on detected emotion.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(EmotionDetectionError, emotion_detection_error_handler)
app.add_exception_handler(AudioSynthesisError, audio_synthesis_error_handler)

# Mount router
app.include_router(router, prefix="/api")
