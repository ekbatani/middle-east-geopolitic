from mei.application.services.forecast_audit import calculate_brier_score
from mei.shared.enums import ForecastOutcome


def test_perfect_yes_prediction_scores_zero() -> None:
    assert calculate_brier_score(1.0, ForecastOutcome.YES) == 0.0


def test_perfect_no_prediction_scores_zero() -> None:
    assert calculate_brier_score(0.0, ForecastOutcome.NO) == 0.0


def test_worst_possible_prediction_scores_one() -> None:
    assert calculate_brier_score(1.0, ForecastOutcome.NO) == 1.0
    assert calculate_brier_score(0.0, ForecastOutcome.YES) == 1.0


def test_fifty_fifty_prediction_scores_quarter_regardless_of_outcome() -> None:
    assert calculate_brier_score(0.5, ForecastOutcome.YES) == 0.25
    assert calculate_brier_score(0.5, ForecastOutcome.NO) == 0.25


def test_ambiguous_outcome_yields_no_score() -> None:
    assert calculate_brier_score(0.7, ForecastOutcome.AMBIGUOUS) is None


def test_brier_score_is_always_between_zero_and_one() -> None:
    for probability in (0.0, 0.1, 0.3, 0.5, 0.8, 1.0):
        for outcome in (ForecastOutcome.YES, ForecastOutcome.NO):
            score = calculate_brier_score(probability, outcome)
            assert score is not None
            assert 0.0 <= score <= 1.0
