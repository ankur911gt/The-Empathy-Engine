import logging
import re
from dataclasses import dataclass

from app.core.exceptions import EmotionDetectionError
from app.core.local_model import get_local_pipeline

logger = logging.getLogger(__name__)

VALID_EMOTIONS = {"joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"}


@dataclass
class EmotionResult:
    emotion: str
    intensity: float
    all_scores: dict[str, float]
    detection_source: str


# =============================================================================
# Keyword-based score boosting
# When the model is uncertain (top score < 0.5 or close margins), these keyword
# patterns boost the relevant emotion's score to correct common misclassifications.
# =============================================================================

_EMOTION_KEYWORDS = {
    "anger": {
        # Strong anger indicators
        "strong": ["hate", "furious", "enraged", "livid", "outraged", "infuriated",
                    "unbelievable", "unacceptable", "disgusted", "sick of", "fed up",
                    "pissed", "ruined", "destroyed"],
        # Moderate anger indicators  
        "moderate": ["angry", "annoyed", "frustrated", "irritated", "mad",
                     "ignored", "disrespected", "unfair", "wrong", "stupid",
                     "ridiculous", "terrible", "awful", "worst"],
        # Anger patterns (regex)
        "patterns": [r"\bNEVER\b", r"\bSTOP\b", r"\bENOUGH\b", r"\bHOW DARE\b",
                     r"\bNO MORE\b", r"!{2,}", r"\bALWAYS\b.*\bnever\b"],
    },
    "joy": {
        "strong": ["ecstatic", "thrilled", "overjoyed", "elated", "euphoric",
                    "amazing", "wonderful", "incredible", "fantastic", "brilliant",
                    "best day", "dream come true", "so proud", "finally did it"],
        "moderate": ["happy", "glad", "excited", "great", "love", "beautiful",
                     "awesome", "perfect", "proud", "celebrate", "grateful",
                     "thankful", "blessed", "lucky", "promoted"],
        "patterns": [r"can't wait", r"so happy", r"love (this|it|you)", r"!{1,}$"],
    },
    "sadness": {
        "strong": ["heartbroken", "devastated", "grieving", "mourning", "hopeless",
                    "nothing left", "all alone", "lost everything", "never recover",
                    "unbearable", "inconsolable"],
        "moderate": ["sad", "miss", "lonely", "empty", "depressed", "cry", "tears",
                     "gone", "lost", "pain", "hurt", "sorry", "regret", "wish",
                     "used to", "remember when", "never coming back"],
        "patterns": [r"I (miss|lost)", r"never (see|hear|feel)", r"if only",
                     r"what (we|I) had", r"gone forever"],
    },
    "fear": {
        "strong": ["terrified", "petrified", "horrified", "nightmare", "panic",
                    "dread", "terror", "paralyzed", "shaking"],
        "moderate": ["scared", "afraid", "worried", "anxious", "nervous", "uneasy",
                     "frightened", "danger", "threat", "dark", "alone", "trapped",
                     "can't breathe", "what if"],
        "patterns": [r"what if", r"I (can't|don't know)", r"something (is|might)",
                     r"broke in", r"hear(d)? (something|a noise)"],
    },
    "surprise": {
        "strong": ["shocked", "stunned", "speechless", "unbelievable", "jaw dropped",
                    "mind blown", "no way", "can't believe"],
        "moderate": ["surprised", "unexpected", "suddenly", "wow", "wait what",
                     "really", "seriously", "actually won", "out of nowhere",
                     "never expected", "didn't see", "caught off guard"],
        "patterns": [r"wait,?\s*(you're|what)", r"I (actually|never) (thought|expected)",
                     r"out of .* people", r"no way"],
    },
    "disgust": {
        "strong": ["revolting", "repulsive", "sickening", "vile", "nauseating",
                    "stomach turn", "makes me sick", "disgusting"],
        "moderate": ["gross", "nasty", "unpleasant", "rude", "disrespectful",
                     "tasteless", "offensive", "inappropriate", "uncomfortable",
                     "careless", "shameful"],
        "patterns": [r"how (could|dare)", r"absolutely (disgusting|revolting)",
                     r"no reason at all"],
    },
}

# Boost amounts
_STRONG_BOOST = 0.25
_MODERATE_BOOST = 0.12
_PATTERN_BOOST = 0.15


def _compute_keyword_boosts(text: str) -> dict[str, float]:
    """Scan text for emotion keywords and return score boosts per emotion."""
    text_lower = text.lower()
    boosts = {}

    for emotion, keywords in _EMOTION_KEYWORDS.items():
        boost = 0.0

        # Check strong keywords
        for word in keywords["strong"]:
            if word in text_lower:
                boost += _STRONG_BOOST
                break  # One strong match is enough

        # Check moderate keywords (count matches for cumulative boost)
        moderate_matches = sum(1 for word in keywords["moderate"] if word in text_lower)
        boost += min(moderate_matches * 0.06, _MODERATE_BOOST)

        # Check regex patterns
        for pattern in keywords["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                boost += _PATTERN_BOOST
                break  # One pattern match is enough

        if boost > 0:
            boosts[emotion] = boost

    return boosts


def _apply_boosts(all_scores: dict[str, float], boosts: dict[str, float]) -> dict[str, float]:
    """Apply keyword boosts to model scores and re-normalize."""
    adjusted = dict(all_scores)

    for emotion, boost in boosts.items():
        if emotion in adjusted:
            adjusted[emotion] = min(adjusted[emotion] + boost, 1.0)

    # Re-normalize so scores sum to ~1.0
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v / total for k, v in adjusted.items()}

    return adjusted


async def detect_emotion(text: str) -> EmotionResult:
    """Detect emotion from text using local transformers pipeline + keyword boosting."""
    try:
        pipeline = get_local_pipeline()
        scores_list = pipeline(text, top_k=None)
        raw_scores = {item["label"]: item["score"] for item in scores_list}

        # Apply keyword-based score boosting
        boosts = _compute_keyword_boosts(text)
        if boosts:
            adjusted_scores = _apply_boosts(raw_scores, boosts)
            logger.info(f"Keyword boosts applied: {boosts}")
        else:
            adjusted_scores = raw_scores

        # Find top emotion from adjusted scores
        emotion = max(adjusted_scores, key=adjusted_scores.get)
        intensity = adjusted_scores[emotion]

        if emotion not in VALID_EMOTIONS:
            logger.warning(f"Unknown emotion '{emotion}' — defaulting to 'neutral'")
            emotion = "neutral"

        logger.info(f"Detected: {emotion} ({intensity:.2f}) | raw_top={max(raw_scores, key=raw_scores.get)}")

        return EmotionResult(
            emotion=emotion,
            intensity=intensity,
            all_scores=adjusted_scores,
            detection_source="local",
        )
    except Exception as e:
        raise EmotionDetectionError(f"Emotion detection failed: {str(e)}") from e
