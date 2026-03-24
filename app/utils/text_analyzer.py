import re
from dataclasses import dataclass, field


@dataclass
class TextAnalysis:
    sentences: list[str]
    sentence_terminals: list[str]
    stress_words: list[str]
    clause_boundaries: list[tuple[int, int]]


# Words that are always considered stress words (case-insensitive match)
_STRESS_WORD_SET = {
    "never", "not", "absolutely", "completely", "always",
    "nothing", "everything", "impossible", "unbelievable",
}

# Regex for repeated vowel sequences (3+ consecutive vowels)
_REPEATED_VOWEL_RE = re.compile(r"[aeiou]{3,}", re.IGNORECASE)


def analyze_text(text: str) -> TextAnalysis:
    """Analyze text for sentence structure, stress words, and clause boundaries."""
    sentences = _split_sentences(text)
    sentence_terminals = [_detect_terminal(s) for s in sentences]
    stress_words = _find_stress_words(text)
    clause_boundaries = _find_clause_boundaries(sentences)

    return TextAnalysis(
        sentences=sentences,
        sentence_terminals=sentence_terminals,
        stress_words=stress_words,
        clause_boundaries=clause_boundaries,
    )


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences at . ? ! ... boundaries."""
    # Strategy: use regex to split while keeping the terminal punctuation attached
    # Handle ellipsis first, then normal terminals
    # Pattern explanation:
    # - \.\.\.(?:\s|$) — ellipsis followed by space or end
    # - (?<![A-Z])\.(?:\s|$) — period not preceded by single uppercase letter, followed by space/end
    # - \?(?:\s|$) — question mark followed by space or end
    # - !(?:\s|$) — exclamation followed by space or end

    if not text.strip():
        return [text] if text else []

    result = []
    current = ""
    i = 0
    chars = text

    while i < len(chars):
        # Check for ellipsis (... or …)
        if chars[i] == "…" or (chars[i] == "." and i + 2 < len(chars) and chars[i + 1] == "." and chars[i + 2] == "."):
            if chars[i] == "…":
                current += "…"
                i += 1
            else:
                current += "..."
                i += 3
            # Check if followed by space or end
            if i >= len(chars) or chars[i] == " ":
                result.append(current.strip())
                current = ""
                if i < len(chars) and chars[i] == " ":
                    i += 1
                continue
            else:
                continue

        # Check for period
        if chars[i] == ".":
            # Check abbreviation: single uppercase letter before the period
            if current and len(current) >= 1:
                # Find the last word character before the period
                stripped = current.rstrip()
                if stripped and len(stripped) >= 1:
                    # Check if the character right before the dot is a single uppercase letter
                    # by checking if the previous non-space char is uppercase and preceded by
                    # a non-alpha or start
                    last_char = stripped[-1]
                    before_last = stripped[-2] if len(stripped) >= 2 else ""
                    if last_char.isupper() and (not before_last or not before_last.isalpha()):
                        # Abbreviation — don't split
                        current += "."
                        i += 1
                        continue

            current += "."
            i += 1
            # Check if followed by space or end
            if i >= len(chars) or chars[i] == " ":
                result.append(current.strip())
                current = ""
                if i < len(chars) and chars[i] == " ":
                    i += 1
                continue
            else:
                continue

        # Check for ? or !
        if chars[i] in ("?", "!"):
            current += chars[i]
            i += 1
            if i >= len(chars) or chars[i] == " ":
                result.append(current.strip())
                current = ""
                if i < len(chars) and chars[i] == " ":
                    i += 1
                continue
            else:
                continue

        current += chars[i]
        i += 1

    # Add remaining text
    if current.strip():
        result.append(current.strip())

    return result if result else [text.strip()] if text.strip() else []


def _detect_terminal(sentence: str) -> str:
    """Detect the terminal type of a sentence."""
    s = sentence.rstrip()
    if s.endswith("...") or s.endswith("…"):
        return "trailing"
    if s.endswith("?"):
        return "question"
    if s.endswith("!"):
        return "exclamation"
    return "statement"


def _find_stress_words(text: str) -> list[str]:
    """Find words matching stress criteria."""
    # Split text into word tokens, keeping track of what follows each word
    stress = []
    # Use regex to find words with their trailing context
    word_pattern = re.compile(r"[A-Za-z']+")

    for match in word_pattern.finditer(text):
        word = match.group()
        end_pos = match.end()

        # Check: entirely uppercase and length >= 2
        if word.isupper() and len(word) >= 2:
            if word not in stress:
                stress.append(word)
            continue

        # Check: immediately followed by !
        if end_pos < len(text) and text[end_pos] == "!":
            if word not in stress:
                stress.append(word)
            continue

        # Check: in the stress word set (case-insensitive)
        if word.lower() in _STRESS_WORD_SET:
            if word not in stress:
                stress.append(word)
            continue

        # Check: contains repeated vowel sequence (3+ consecutive vowels)
        if _REPEATED_VOWEL_RE.search(word):
            if word not in stress:
                stress.append(word)
            continue

    return stress


def _find_clause_boundaries(sentences: list[str]) -> list[tuple[int, int]]:
    """Find clause boundaries (commas, semicolons, em-dashes) in sentences."""
    boundaries = []
    clause_chars = {",", ";", "—", "–"}

    for sent_idx, sentence in enumerate(sentences):
        for char_offset, char in enumerate(sentence):
            if char in clause_chars:
                boundaries.append((sent_idx, char_offset))

    return boundaries
