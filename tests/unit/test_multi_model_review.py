from hypothesis import given
from hypothesis import strategies as st

from mei.application.services.multi_model_review import (
    classify_agreement,
    should_trigger_for_risk,
)


def test_no_previous_score_never_triggers() -> None:
    assert should_trigger_for_risk(90, None, threshold=15) is None


def test_small_move_does_not_trigger() -> None:
    assert should_trigger_for_risk(55, 50, threshold=15) is None


def test_move_at_threshold_triggers() -> None:
    assert should_trigger_for_risk(65, 50, threshold=15) == "score_delta"


def test_large_downward_move_triggers() -> None:
    assert should_trigger_for_risk(20, 80, threshold=15) == "score_delta"


def test_agreement_within_tolerance() -> None:
    assert classify_agreement(70, 74, tolerance=5) is True


def test_agreement_at_exact_tolerance_boundary() -> None:
    assert classify_agreement(70, 75, tolerance=5) is True


def test_disagreement_beyond_tolerance() -> None:
    assert classify_agreement(70, 76, tolerance=5) is False


@given(
    final_score=st.integers(min_value=0, max_value=100),
    previous_score=st.integers(min_value=0, max_value=100),
    threshold=st.integers(min_value=1, max_value=100),
)
def test_trigger_is_monotonic_in_delta_magnitude(
    final_score: int, previous_score: int, threshold: int
) -> None:
    delta = abs(final_score - previous_score)
    triggered = should_trigger_for_risk(final_score, previous_score, threshold)
    assert (triggered == "score_delta") == (delta >= threshold)


@given(
    primary=st.integers(min_value=0, max_value=100),
    secondary=st.integers(min_value=0, max_value=100),
    tolerance=st.integers(min_value=0, max_value=100),
)
def test_classify_agreement_is_symmetric(primary: int, secondary: int, tolerance: int) -> None:
    assert classify_agreement(primary, secondary, tolerance) == classify_agreement(
        secondary, primary, tolerance
    )
