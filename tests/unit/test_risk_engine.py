from hypothesis import given
from hypothesis import strategies as st

from mei.application.services.risk_engine import (
    ContributionRecord,
    aggregate_contributions,
    diff_changed_indicators,
)


def _record(
    *,
    code: str = "indicator",
    weight: float = 1.0,
    normalized_value: float | None = 0.5,
    direction: str = "positive",
    confidence: float | None = 1.0,
    included: bool = True,
    stale: bool = False,
) -> ContributionRecord:
    contribution = None
    if normalized_value is not None:
        contribution = normalized_value if direction == "positive" else 1.0 - normalized_value
    return ContributionRecord(
        indicator_code=code,
        indicator_name=code.replace("_", " ").title(),
        weight=weight,
        direction=direction,
        raw_value=normalized_value,
        normalized_value=normalized_value,
        contribution=contribution if included else None,
        confidence=confidence if included else None,
        observed_at="2026-07-21T00:00:00+00:00" if included else None,
        included=included,
        stale=stale,
    )


def test_full_weight_and_max_normalized_value_yields_max_score() -> None:
    contributions = [_record(normalized_value=1.0, weight=1.0)]
    base_score, confidence, available_weight = aggregate_contributions(
        contributions, total_weight=1.0
    )
    assert base_score == 100
    assert confidence == 1.0
    assert available_weight == 1.0


def test_zero_normalized_value_yields_zero_score() -> None:
    contributions = [_record(normalized_value=0.0, weight=1.0)]
    base_score, _, _ = aggregate_contributions(contributions, total_weight=1.0)
    assert base_score == 0


def test_inverse_direction_flips_contribution() -> None:
    positive = aggregate_contributions(
        [_record(normalized_value=0.9, direction="positive", weight=1.0)], total_weight=1.0
    )
    inverse = aggregate_contributions(
        [_record(normalized_value=0.9, direction="inverse", weight=1.0)], total_weight=1.0
    )
    assert positive[0] == 90
    assert inverse[0] == 10


def test_missing_indicator_is_excluded_not_zeroed() -> None:
    # One indicator at a high value, one entirely missing: the missing one
    # should not drag the score toward zero, only reduce confidence via
    # reduced coverage.
    contributions = [
        _record(code="a", normalized_value=1.0, weight=0.5),
        _record(code="b", normalized_value=None, weight=0.5, included=False),
    ]
    base_score, confidence, available_weight = aggregate_contributions(
        contributions, total_weight=1.0
    )
    assert base_score == 100  # only the available indicator counts toward the score
    assert available_weight == 0.5
    assert confidence < 1.0  # coverage gap still reduces confidence


def test_no_available_indicators_yields_zero_score_and_confidence() -> None:
    contributions = [_record(code="a", normalized_value=None, weight=1.0, included=False)]
    base_score, confidence, available_weight = aggregate_contributions(
        contributions, total_weight=1.0
    )
    assert base_score == 0
    assert confidence == 0.0
    assert available_weight == 0.0


def test_low_confidence_observation_reduces_confidence_not_score() -> None:
    high_confidence = aggregate_contributions(
        [_record(normalized_value=0.8, confidence=1.0, weight=1.0)], total_weight=1.0
    )
    low_confidence = aggregate_contributions(
        [_record(normalized_value=0.8, confidence=0.2, weight=1.0)], total_weight=1.0
    )
    assert high_confidence[0] == low_confidence[0]  # score unaffected
    assert low_confidence[1] < high_confidence[1]  # confidence reduced


@given(
    normalized_values=st.lists(
        st.floats(min_value=0, max_value=1, allow_nan=False), min_size=1, max_size=10
    ),
    weights=st.lists(
        st.floats(min_value=0.01, max_value=10, allow_nan=False), min_size=1, max_size=10
    ),
)
def test_base_score_and_confidence_always_within_bounds(
    normalized_values: list[float], weights: list[float]
) -> None:
    size = min(len(normalized_values), len(weights))
    contributions = [
        _record(code=f"i{i}", normalized_value=normalized_values[i], weight=weights[i])
        for i in range(size)
    ]
    total_weight = sum(weights[:size])
    base_score, confidence, _ = aggregate_contributions(contributions, total_weight)
    assert 0 <= base_score <= 100
    assert 0.0 <= confidence <= 1.0


def _as_objects(records: list[ContributionRecord]) -> list[object]:
    # `contributions_json` round-trips through JSONB as `list[object]`
    # (see `RiskAssessment.contributions_json`); ContributionRecord entries
    # are plain dicts at runtime, so this only relabels the static type to
    # match what `diff_changed_indicators` actually receives in production.
    return list(records)


def test_diff_changed_indicators_flags_moved_values() -> None:
    previous = [_record(code="a", normalized_value=0.2), _record(code="b", normalized_value=0.5)]
    current = [_record(code="a", normalized_value=0.9), _record(code="b", normalized_value=0.5)]
    assert diff_changed_indicators(_as_objects(previous), _as_objects(current)) == ["a"]


def test_diff_changed_indicators_ignores_small_moves() -> None:
    previous = [_record(code="a", normalized_value=0.500)]
    current = [_record(code="a", normalized_value=0.510)]
    assert diff_changed_indicators(_as_objects(previous), _as_objects(current), epsilon=0.05) == []


def test_diff_changed_indicators_with_no_prior_history_reports_all_included() -> None:
    current = [_record(code="a"), _record(code="b", included=False)]
    assert diff_changed_indicators(None, _as_objects(current)) == ["a"]
