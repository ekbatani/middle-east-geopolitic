from mei.infrastructure.translation.language_detection import detect_language


def test_detects_english() -> None:
    text = (
        "The ministry confirmed that emergency services responded to the "
        "incident within the hour and that evacuations were underway."
    )
    assert detect_language(text) == "en"


def test_returns_none_for_empty_text() -> None:
    assert detect_language("") is None
    assert detect_language("   ") is None


def test_returns_none_for_undetectable_text() -> None:
    assert detect_language("123 456 789") is None
