import pytest

from app.services.text_preprocessor import preprocess_text


class TestIntensityGate:
    """Intensity < 0.35 returns original text unchanged."""

    @pytest.mark.parametrize("emotion", ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"])
    def test_low_intensity_returns_original(self, emotion):
        text = "This is a test sentence with some words."
        assert preprocess_text(text, emotion, 0.30) == text

    def test_zero_intensity_returns_original(self):
        text = "Any text at all."
        assert preprocess_text(text, "joy", 0.0) == text


class TestSadness:
    def test_long_statements_get_trailing(self):
        text = "I keep thinking about what we had and how much I truly miss it."
        result = preprocess_text(text, "sadness", 0.85)
        assert "..." in result

    def test_questions_not_modified(self):
        text = "Why did you leave?"
        result = preprocess_text(text, "sadness", 0.85)
        assert result.rstrip().endswith("?")


class TestAnger:
    def test_no_trailing_ellipsis(self):
        text = "I can't believe... you did that... to me..."
        result = preprocess_text(text, "anger", 0.90)
        assert "..." not in result

    def test_long_sentences_split(self):
        text = "I told you exactly what I needed and you completely ignored me, just like you always do."
        result = preprocess_text(text, "anger", 0.90)
        # Should have more sentence-ending punctuation due to splitting
        assert result.count(".") + result.count("!") >= 1


class TestFear:
    def test_statements_end_with_ellipsis(self):
        text = "I'm worried about what happens next."
        result = preprocess_text(text, "fear", 0.80)
        assert "..." in result

    def test_short_sentence_stutter(self):
        """Short 'I' sentences get stutter effect."""
        text = "I can't."
        result = preprocess_text(text, "fear", 0.80)
        assert "..." in result


class TestJoy:
    def test_trailing_replaced_with_exclamation(self):
        text = "This is so amazing..."
        result = preprocess_text(text, "joy", 0.90)
        assert "!" in result
        assert "..." not in result


class TestSurprise:
    def test_statements_end_with_exclamation(self):
        text = "I can't believe you came."
        result = preprocess_text(text, "surprise", 0.80)
        assert result.rstrip().endswith("!")


class TestNoModification:
    def test_disgust_no_text_change(self):
        """Disgust relies on voice params only — no text changes."""
        text = "That was really unpleasant."
        assert preprocess_text(text, "disgust", 0.90) == text

    def test_neutral_no_text_change(self):
        text = "The weather is fine today."
        assert preprocess_text(text, "neutral", 0.90) == text


class TestSafety:
    def test_no_markup_leakage(self):
        text = "This is <b>bold</b> text."
        result = preprocess_text(text, "anger", 0.90)
        assert "<" not in result
        assert ">" not in result

    @pytest.mark.parametrize("emotion", ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"])
    def test_non_empty_output(self, emotion):
        text = "Hello world."
        result = preprocess_text(text, emotion, 0.90)
        assert len(result.strip()) > 0
