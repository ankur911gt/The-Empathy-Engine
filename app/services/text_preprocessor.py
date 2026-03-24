import re

from app.utils.text_analyzer import analyze_text


def preprocess_text(text: str, emotion: str, intensity: float) -> str:
    """Enrich text with strategic punctuation based on detected emotion and intensity.
    
    Neural TTS engines naturally respond to punctuation cues:
    - Ellipsis (...) → creates natural pauses, trailing off
    - Exclamation (!) → creates emphasis, upward inflection
    - Comma (,) → brief pause
    - Period (.) → hard stop, downward inflection
    - Question mark (?) → rising inflection
    
    We exploit these to enhance emotional delivery without SSML.
    """

    # Intensity gate: no enrichment for low-confidence detections
    if intensity < 0.35:
        return text

    analysis = analyze_text(text)
    sentences = list(analysis.sentences)
    terminals = list(analysis.sentence_terminals)
    stress_words = set(w.lower() for w in analysis.stress_words)

    if emotion == "sadness":
        sentences = _process_sadness(sentences, terminals, stress_words)
    elif emotion == "anger":
        sentences = _process_anger(sentences, terminals)
    elif emotion == "fear":
        sentences = _process_fear(sentences, terminals)
    elif emotion == "joy":
        sentences = _process_joy(sentences, terminals)
    elif emotion == "surprise":
        sentences = _process_surprise(sentences, terminals)
    # disgust and neutral: no text modifications (handled by voice params only)

    result = " ".join(sentences)

    # Safety: strip any HTML/XML tags
    result = result.replace("<", "").replace(">", "")

    return result


def _wc(sentence: str) -> int:
    """Word count helper."""
    return len(sentence.split())


# =============================================================================
# SADNESS: Heavy, weary, trailing, slow
# Key techniques: trailing ellipsis, weary pauses after commas, mid-sentence breaks
# =============================================================================
def _process_sadness(sentences, terminals, stress_words):
    result = []
    for i, sentence in enumerate(sentences):
        s = sentence

        # 1. After commas that precede stress words, add weary pause ,...
        parts = s.split(",")
        rebuilt = [parts[0]]
        for j in range(1, len(parts)):
            stripped = parts[j].strip()
            first_word = stripped.split()[0].lower() if stripped.split() else ""
            if first_word in stress_words:
                rebuilt.append(",... " + stripped)
            else:
                rebuilt.append(", " + stripped)
        s = "".join(rebuilt)

        # 2. Long statements (8+ words) trail off with ...
        if terminals[i] == "statement" and _wc(s) > 8:
            s = _replace_ending(s, ".", "...")

        # 3. Insert a breathing comma in the middle of longer sentences
        if _wc(s) > 6:
            words = s.split()
            mid = len(words) // 2
            if not words[mid].endswith(","):
                words[mid] = words[mid] + ","
            s = " ".join(words)

        # 4. For very long sentences, add a second pause at 75%
        if _wc(s) > 14:
            words = s.split()
            q3 = int(len(words) * 0.75)
            if not words[q3].endswith((",", ".", "...", "!")):
                words[q3] = words[q3] + ",..."
            s = " ".join(words)

        result.append(s)
    return result


# =============================================================================
# ANGER: Punchy, forceful, short sentences, hard stops, no trailing
# Key techniques: remove ellipsis, split long sentences, add ! to short fragments
# =============================================================================
def _process_anger(sentences, terminals):
    result = []
    for i, sentence in enumerate(sentences):
        s = sentence

        # 1. Remove ALL trailing ellipsis — anger doesn't trail off, it HITS
        s = s.replace("...", ".")
        s = s.replace("…", ".")
        # Clean double periods
        while ".." in s:
            s = s.replace("..", ".")

        # 2. Split long sentences (12+ words) at the nearest comma/semicolon to midpoint
        if _wc(s) > 12:
            split_result = _split_at_clause(s)
            if split_result:
                result.extend(split_result)
                continue

        # 3. Short emphatic statements (≤5 words) → exclamation
        if _wc(s) <= 5 and terminals[i] == "statement":
            s = _replace_ending(s, ".", "!")

        # 4. Even medium statements get harder endings
        if terminals[i] == "statement" and _wc(s) <= 8:
            s = _replace_ending(s, ".", "!")

        result.append(s)
    return result


# =============================================================================
# FEAR: Hesitant, fragmented, breathless, trailing uncertainty
# Key techniques: mid-sentence ellipsis, word stutters, trailing ...
# =============================================================================
def _process_fear(sentences, terminals):
    result = []
    for i, sentence in enumerate(sentences):
        s = sentence

        # 1. Long sentences (10+ words) → insert hesitation "..." near 60% mark
        if _wc(s) > 10:
            target_pos = int(len(s) * 0.6)
            best_pos = _find_nearest_punct(s, target_pos, (",", ";"))
            if best_pos > 0:
                s = s[:best_pos] + "..." + s[best_pos + 1:]

        # 2. Short sentences starting with I/it/what/this → stutter
        if _wc(s) <= 6 and terminals[i] == "statement":
            first_word = s.split()[0] if s.split() else ""
            if first_word.lower() in ("i", "it", "what", "this", "that", "we"):
                s = first_word + "... " + s

        # 3. ALL statements trail off with ... (fear never resolves)
        if terminals[i] == "statement":
            s = _ensure_trailing(s, "...")

        # 4. Questions get trailing too (uncertainty)
        if terminals[i] == "question" and _wc(s) > 5:
            stripped = s.rstrip()
            if stripped.endswith("?"):
                s = stripped[:-1] + "...?"

        result.append(s)
    return result


# =============================================================================
# JOY: Upbeat, exclamatory, energetic, no fading
# Key techniques: replace ... with !, add ! to statements
# =============================================================================
def _process_joy(sentences, terminals):
    result = []
    for i, sentence in enumerate(sentences):
        s = sentence

        # 1. Replace ALL trailing ... with ! — joy doesn't fade, it lands
        s = s.replace("...", "!")
        s = s.replace("…", "!")
        # Clean multiple exclamations
        while "!!" in s:
            s = s.replace("!!", "!")

        # 2. Statements get exclamation endings
        if terminals[i] == "statement":
            s = _replace_ending(s, ".", "!")

        result.append(s)
    return result


# =============================================================================
# SURPRISE: Startled, emphatic, rising inflection
# Key techniques: all statements → !, short sentences get emphasis
# =============================================================================
def _process_surprise(sentences, terminals):
    result = []
    for i, sentence in enumerate(sentences):
        s = sentence

        # 1. All statements become exclamations
        if terminals[i] == "statement":
            s = _replace_ending(s, ".", "!")
            # Also ensure it ends with ! if it doesn't end with ? or !
            stripped = s.rstrip()
            if not stripped.endswith(("!", "?", "...")):
                s = stripped + "!"

        result.append(s)
    return result


# =============================================================================
# Utility functions
# =============================================================================

def _replace_ending(s: str, old_end: str, new_end: str) -> str:
    """Replace the sentence-ending punctuation."""
    stripped = s.rstrip()
    if stripped.endswith("..."):
        return stripped[:-3] + new_end
    if stripped.endswith(old_end):
        return stripped[:-len(old_end)] + new_end
    return s


def _ensure_trailing(s: str, trail: str) -> str:
    """Ensure a sentence ends with the given trailing punctuation."""
    stripped = s.rstrip()
    if stripped.endswith("...") or stripped.endswith("…"):
        return s
    if stripped.endswith("."):
        return stripped[:-1] + trail
    if not stripped.endswith(("!", "?", "...")):
        return stripped + trail
    return s


def _find_nearest_punct(s: str, target_pos: int, chars: tuple) -> int:
    """Find the position of the nearest punctuation character to target_pos."""
    best_pos = -1
    best_dist = len(s)
    for pos, char in enumerate(s):
        if char in chars:
            dist = abs(pos - target_pos)
            if dist < best_dist:
                best_dist = dist
                best_pos = pos
    return best_pos


def _split_at_clause(s: str) -> list[str] | None:
    """Split a long sentence at its middle clause boundary. Returns None if no split."""
    midpoint = len(s) // 2
    best_pos = _find_nearest_punct(s, midpoint, (",", ";"))
    if best_pos <= 0:
        return None

    first = s[:best_pos].rstrip()
    second = s[best_pos + 1:].lstrip()

    if not first.endswith((".", "!", "?")):
        first += "."
    if second:
        second = second[0].upper() + second[1:] if len(second) > 1 else second.upper()

    parts = [first]
    if second:
        parts.append(second)
    return parts
