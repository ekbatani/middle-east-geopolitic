from hypothesis import given
from hypothesis import strategies as st

from mei.application.services.analyst_disagreement import classify_disagreement


def test_unanimous_stance_with_tight_scores_is_not_disagreement() -> None:
    assert classify_disagreement(["agree", "agree", "agree"], [70.0, 72.0, 71.0]) is False


def test_two_distinct_stances_is_always_disagreement() -> None:
    assert classify_disagreement(["agree", "disagree"], [None, None]) is True


def test_three_distinct_stances_is_disagreement() -> None:
    assert classify_disagreement(["agree", "uncertain", "disagree"], [50.0, 50.0, 50.0]) is True


def test_wide_score_spread_with_same_stance_is_disagreement() -> None:
    assert classify_disagreement(["agree", "agree"], [10.0, 90.0], score_threshold=20.0) is True


def test_score_spread_below_threshold_is_not_disagreement() -> None:
    assert classify_disagreement(["agree", "agree"], [40.0, 55.0], score_threshold=20.0) is False


def test_single_position_is_never_disagreement() -> None:
    assert classify_disagreement(["agree"], [80.0]) is False


def test_all_none_stances_and_scores_is_not_disagreement() -> None:
    assert classify_disagreement([None, None], [None, None]) is False


@given(stance=st.sampled_from(["agree", "disagree", "uncertain"]), count=st.integers(min_value=1, max_value=10))
def test_unanimous_stance_never_flags_regardless_of_count(stance: str, count: int) -> None:
    assert classify_disagreement([stance] * count, [None] * count) is False


@given(
    stances=st.lists(st.sampled_from(["agree", "disagree"]), min_size=2, max_size=10).filter(
        lambda values: len(set(values)) >= 2
    )
)
def test_any_two_distinct_stances_always_flags(stances: list[str]) -> None:
    assert classify_disagreement(stances, [None] * len(stances)) is True
