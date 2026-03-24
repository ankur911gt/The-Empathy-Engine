from typing import Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    emotion: Optional[str] = Field(None, description="Force a specific emotion (for comparison mode)")


class VoiceParams(BaseModel):
    rate: str
    pitch: str
    volume: str
    voice: str


class AnalyzeResponse(BaseModel):
    emotion: str
    intensity: float
    all_scores: dict[str, float]
    detection_source: str
    voice_params: VoiceParams
    original_text: str
    processed_text: str
    ssml_text: str
    audio_url: str
    processing_time_ms: float


class HealthResponse(BaseModel):
    status: str
    hf_model_loaded: bool
