import logging
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # HuggingFace Inference API
    hf_api_token: str = ""
    hf_model_name: str = "j-hartmann/emotion-english-distilroberta-base"
    hf_api_timeout_seconds: int = 4

    # ElevenLabs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    elevenlabs_model_id: str = "eleven_multilingual_v2"

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    audio_output_dir: str = "outputs"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
