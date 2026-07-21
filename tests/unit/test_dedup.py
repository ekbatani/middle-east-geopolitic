from mei.infrastructure.collection.dedup import compute_fingerprint

_ARTICLE = """Officials in the region reported a significant escalation
overnight, with multiple strikes hitting infrastructure targets. Emergency
services responded within the hour and evacuations began shortly after."""


def test_fingerprint_is_deterministic() -> None:
    assert compute_fingerprint(_ARTICLE) == compute_fingerprint(_ARTICLE)


def test_fingerprint_matches_for_identical_text_via_different_mirrors() -> None:
    mirror = _ARTICLE  # same wire-service text republished verbatim elsewhere
    assert compute_fingerprint(_ARTICLE) == compute_fingerprint(mirror)


def test_fingerprint_differs_for_unrelated_text() -> None:
    other = "A completely unrelated story about agricultural exports and trade policy."
    assert compute_fingerprint(_ARTICLE) != compute_fingerprint(other)


def test_fingerprint_of_empty_text_is_stable_sentinel() -> None:
    assert compute_fingerprint("") == compute_fingerprint("")
    assert compute_fingerprint("") == "0" * 16


def test_fingerprint_is_fixed_length_hex() -> None:
    fingerprint = compute_fingerprint(_ARTICLE)
    assert len(fingerprint) == 16
    int(fingerprint, 16)  # raises ValueError if not valid hex
