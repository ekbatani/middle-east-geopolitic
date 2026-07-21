from langdetect import DetectorFactory, LangDetectException, detect

# langdetect's detector is seeded from system randomness by default, which
# makes short/ambiguous text non-reproducible across runs; pin it so results
# are deterministic (matters for tests and for debugging a specific
# document's detected language).
DetectorFactory.seed = 0


def detect_language(text: str) -> str | None:
    """Best-effort ISO 639-1 language code, or `None` if undetectable.

    Short or ambiguous text raises inside `langdetect`; that's treated as
    "unknown" rather than propagated, since a document's language being
    unclear shouldn't fail the pipeline (translation is simply skipped).
    """
    if not text or not text.strip():
        return None
    try:
        return str(detect(text))
    except LangDetectException:
        return None


__all__ = ["detect_language"]
