import logging

from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline as hf_pipeline

from app.core.config import settings

logger = logging.getLogger(__name__)

_pipeline = None
_tokenizer = None
_model = None


def get_local_pipeline():
    """Lazy singleton for the local CPU pipeline. Loaded on first call."""
    global _pipeline, _tokenizer, _model

    if _pipeline is None:
        model_name = settings.hf_model_name
        logger.info(f"Loading model: {model_name}")

        # Load tokenizer and model directly
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModelForSequenceClassification.from_pretrained(model_name)

        # Build pipeline using the loaded model and tokenizer
        _pipeline = hf_pipeline(
            "text-classification",
            model=_model,
            tokenizer=_tokenizer,
            top_k=None,
        )
        logger.info(f"Local CPU pipeline loaded: {model_name}")

    return _pipeline
