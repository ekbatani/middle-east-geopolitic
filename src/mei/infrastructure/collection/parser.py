import trafilatura

PARSER_VERSION = "trafilatura-generic-v1"
DEFAULT_CHUNK_CHARS = 4000


def extract_text(body: bytes, *, url: str | None = None) -> str | None:
    """Extract the main article text from raw HTML bytes.

    Uses a generic extractor for every source, per section 10.5 of the
    implementation design: source-specific adapters are added later only
    where quality requires them.
    """
    extracted = trafilatura.extract(
        body,
        url=url,
        include_comments=False,
        favor_precision=True,
    )
    return extracted.strip() if extracted else None


def chunk_text(text: str, *, max_chars: int = DEFAULT_CHUNK_CHARS) -> list[str]:
    """Split text into paragraph-aligned chunks no larger than `max_chars`."""
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks or [text]


__all__ = ["PARSER_VERSION", "chunk_text", "extract_text"]
