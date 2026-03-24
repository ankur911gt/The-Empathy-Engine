import hashlib

_cache: dict[str, tuple[bytes, str]] = {}
CACHE_MAX_SIZE = 100


def get_cached(cache_key: str) -> tuple[bytes, str] | None:
    """Returns the cached (audio_bytes, filename) if the key exists, else None."""
    return _cache.get(cache_key)


def set_cached(cache_key: str, audio_bytes: bytes, filename: str) -> None:
    """Store audio in cache. Evicts oldest entry if cache is full."""
    if len(_cache) >= CACHE_MAX_SIZE:
        oldest_key = next(iter(_cache))
        del _cache[oldest_key]
    _cache[cache_key] = (audio_bytes, filename)


def make_cache_key(text: str, emotion: str, intensity: float) -> str:
    """Construct SHA-256 cache key from text, emotion, and intensity bucket."""
    intensity_bucket = round(intensity, 1)
    key_string = f"{text}|{emotion}|{intensity_bucket}"
    return hashlib.sha256(key_string.encode()).hexdigest()
