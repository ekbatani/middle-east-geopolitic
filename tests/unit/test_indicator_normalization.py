import pytest
from hypothesis import given
from hypothesis import strategies as st

from mei.application.services.indicators import normalize_value
from mei.shared.enums import IndicatorNormalizationMethod
from mei.shared.errors import ValidationError


def test_min_max_scales_to_unit_interval() -> None:
    result = normalize_value(
        5, method=IndicatorNormalizationMethod.MIN_MAX, lower_bound=0, upper_bound=10
    )
    assert result == pytest.approx(0.5)


def test_min_max_clamps_below_lower_bound() -> None:
    result = normalize_value(
        -5, method=IndicatorNormalizationMethod.MIN_MAX, lower_bound=0, upper_bound=10
    )
    assert result == 0.0


def test_min_max_clamps_above_upper_bound() -> None:
    result = normalize_value(
        50, method=IndicatorNormalizationMethod.MIN_MAX, lower_bound=0, upper_bound=10
    )
    assert result == 1.0


def test_min_max_requires_bounds() -> None:
    with pytest.raises(ValidationError):
        normalize_value(
            5, method=IndicatorNormalizationMethod.MIN_MAX, lower_bound=None, upper_bound=10
        )


def test_min_max_rejects_degenerate_bounds() -> None:
    with pytest.raises(ValidationError):
        normalize_value(
            5, method=IndicatorNormalizationMethod.MIN_MAX, lower_bound=10, upper_bound=10
        )


@pytest.mark.parametrize("raw_value,expected", [(0, 0.0), (1, 1.0), (-3, 1.0), (0.0, 0.0)])
def test_boolean_maps_nonzero_to_one(raw_value: float, expected: float) -> None:
    assert (
        normalize_value(
            raw_value,
            method=IndicatorNormalizationMethod.BOOLEAN,
            lower_bound=None,
            upper_bound=None,
        )
        == expected
    )


def test_manual_passes_through_within_range() -> None:
    assert (
        normalize_value(
            0.42, method=IndicatorNormalizationMethod.MANUAL, lower_bound=None, upper_bound=None
        )
        == 0.42
    )


def test_manual_clamps_out_of_range() -> None:
    assert (
        normalize_value(
            5, method=IndicatorNormalizationMethod.MANUAL, lower_bound=None, upper_bound=None
        )
        == 1.0
    )
    assert (
        normalize_value(
            -5, method=IndicatorNormalizationMethod.MANUAL, lower_bound=None, upper_bound=None
        )
        == 0.0
    )


@given(
    raw_value=st.floats(allow_nan=False, allow_infinity=False, width=32),
    lower_bound=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
    span=st.floats(min_value=1e-3, max_value=1e6, allow_nan=False),
)
def test_min_max_always_within_unit_interval(
    raw_value: float, lower_bound: float, span: float
) -> None:
    upper_bound = lower_bound + span
    result = normalize_value(
        raw_value,
        method=IndicatorNormalizationMethod.MIN_MAX,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )
    assert 0.0 <= result <= 1.0
