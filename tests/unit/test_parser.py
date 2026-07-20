from mei.infrastructure.collection.parser import chunk_text, extract_text


def test_chunk_text_empty_returns_empty_list() -> None:
    assert chunk_text("") == []


def test_chunk_text_single_short_paragraph() -> None:
    assert chunk_text("A single short paragraph.") == ["A single short paragraph."]


def test_chunk_text_preserves_paragraph_boundaries_when_small() -> None:
    text = "First paragraph.\n\nSecond paragraph."

    chunks = chunk_text(text, max_chars=1000)

    assert chunks == ["First paragraph.\n\nSecond paragraph."]


def test_chunk_text_splits_when_exceeding_max_chars() -> None:
    paragraph_a = "A" * 50
    paragraph_b = "B" * 50
    text = f"{paragraph_a}\n\n{paragraph_b}"

    chunks = chunk_text(text, max_chars=60)

    assert len(chunks) == 2
    assert chunks[0] == paragraph_a
    assert chunks[1] == paragraph_b


def test_extract_text_pulls_article_body_from_html() -> None:
    html = b"""
    <html><body>
    <article>
        <p>This is the main article content that trafilatura should extract
        and it needs to be reasonably long so the extractor doesn't discard
        it as boilerplate noise during heuristic filtering of short blocks.</p>
    </article>
    </body></html>
    """

    extracted = extract_text(html, url="https://example.com/article")

    assert extracted is not None
    assert "main article content" in extracted


def test_extract_text_returns_none_for_empty_body() -> None:
    assert extract_text(b"") is None
