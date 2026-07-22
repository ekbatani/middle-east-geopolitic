from mei.application.services.investigations import extract_keywords, score_narrative_comparison


def test_extract_keywords_drops_stopwords_and_short_tokens() -> None:
    keywords = extract_keywords("Did State A violate State B's airspace?")
    assert "State" in keywords
    assert "violate" in keywords
    assert "airspace" in keywords
    assert "Did" not in keywords
    assert "A" not in keywords


def test_extract_keywords_deduplicates_case_sensitively() -> None:
    keywords = extract_keywords("border border troops border")
    assert keywords.count("border") == 1


def test_extract_keywords_empty_for_only_stopwords() -> None:
    assert extract_keywords("Is the of and") == []


def test_score_narrative_comparison_no_claims_found() -> None:
    result = score_narrative_comparison(
        claim_count=0, supporting_evidence_count=0, contradicting_evidence_count=0, claim_confidences=[]
    )
    assert result["confidence"] == 0.0
    assert result["divergence_score"] == 0.0
    assert "No claims" in result["comparison_summary"]


def test_score_narrative_comparison_claims_without_confidence_scores_low() -> None:
    result = score_narrative_comparison(
        claim_count=2, supporting_evidence_count=0, contradicting_evidence_count=0, claim_confidences=[]
    )
    assert result["confidence"] == 0.3
    assert "no contradicting evidence" in result["comparison_summary"]


def test_score_narrative_comparison_averages_claim_confidences() -> None:
    result = score_narrative_comparison(
        claim_count=2,
        supporting_evidence_count=1,
        contradicting_evidence_count=1,
        claim_confidences=[0.8, 0.6],
    )
    assert result["confidence"] == 0.7
    assert result["divergence_score"] == 0.5
    assert "disputed narratives" in result["comparison_summary"]


def test_score_narrative_comparison_divergence_is_bounded() -> None:
    result = score_narrative_comparison(
        claim_count=3,
        supporting_evidence_count=0,
        contradicting_evidence_count=5,
        claim_confidences=[0.9],
    )
    assert result["divergence_score"] == 1.0
