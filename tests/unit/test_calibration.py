from hypothesis import given
from hypothesis import strategies as st

from mei.application.services.calibration import ForecastSample, bucket_forecasts
from mei.shared.enums import ForecastOutcome


def _sample(
    probability: float, outcome: ForecastOutcome, brier_score: float | None = None
) -> ForecastSample:
    return ForecastSample(probability=probability, outcome=outcome, brier_score=brier_score)


def test_empty_input_returns_ten_empty_buckets_not_a_crash() -> None:
    buckets = bucket_forecasts([], bucket_count=10)
    assert len(buckets) == 10
    for bucket in buckets:
        assert bucket["forecast_count"] == 0
        assert bucket["mean_predicted_probability"] is None
        assert bucket["observed_frequency"] is None
        assert bucket["mean_brier_score"] is None


def test_bucket_boundaries_partition_zero_to_one_exactly() -> None:
    buckets = bucket_forecasts([], bucket_count=5)
    assert buckets[0]["lower"] == 0.0
    assert buckets[-1]["upper"] == 1.0
    for i in range(len(buckets) - 1):
        assert buckets[i]["upper"] == buckets[i + 1]["lower"]


def test_forecast_at_probability_100_lands_in_last_bucket() -> None:
    samples = [_sample(100.0, ForecastOutcome.YES)]
    buckets = bucket_forecasts(samples, bucket_count=10)
    assert buckets[-1]["forecast_count"] == 1
    assert sum(b["forecast_count"] for b in buckets) == 1


def test_observed_frequency_reflects_yes_no_mix() -> None:
    samples = [
        _sample(70.0, ForecastOutcome.YES),
        _sample(72.0, ForecastOutcome.NO),
        _sample(75.0, ForecastOutcome.YES),
    ]
    buckets = bucket_forecasts(samples, bucket_count=10)
    bucket = next(b for b in buckets if b["forecast_count"] == 3)
    assert bucket["observed_frequency"] == 2 / 3


def test_mean_brier_score_ignores_missing_scores() -> None:
    samples = [
        _sample(50.0, ForecastOutcome.YES, brier_score=0.25),
        _sample(52.0, ForecastOutcome.NO, brier_score=None),
    ]
    buckets = bucket_forecasts(samples, bucket_count=10)
    bucket = next(b for b in buckets if b["forecast_count"] == 2)
    assert bucket["mean_brier_score"] == 0.25


@given(
    probabilities=st.lists(
        st.floats(min_value=0, max_value=100, allow_nan=False), min_size=0, max_size=30
    ),
    bucket_count=st.integers(min_value=1, max_value=20),
)
def test_bucket_counts_always_sum_to_total_samples(
    probabilities: list[float], bucket_count: int
) -> None:
    samples = [_sample(p, ForecastOutcome.YES) for p in probabilities]
    buckets = bucket_forecasts(samples, bucket_count=bucket_count)
    assert len(buckets) == bucket_count
    assert sum(b["forecast_count"] for b in buckets) == len(samples)
