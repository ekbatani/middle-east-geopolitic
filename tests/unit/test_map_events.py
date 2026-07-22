import pytest
from apps.api.routers.intelligence import parse_bbox
from hypothesis import given
from hypothesis import strategies as st

from mei.shared.errors import ValidationError


@given(
    min_lon=st.floats(min_value=-180, max_value=180, allow_nan=False),
    min_lat=st.floats(min_value=-90, max_value=90, allow_nan=False),
    max_lon=st.floats(min_value=-180, max_value=180, allow_nan=False),
    max_lat=st.floats(min_value=-90, max_value=90, allow_nan=False),
)
def test_parse_bbox_round_trips(
    min_lon: float, min_lat: float, max_lon: float, max_lat: float
) -> None:
    value = f"{min_lon},{min_lat},{max_lon},{max_lat}"
    assert parse_bbox(value) == (min_lon, min_lat, max_lon, max_lat)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "1,2,3",
        "1,2,3,4,5",
        "a,b,c,d",
        "1,2,3,notanumber",
    ],
)
def test_parse_bbox_rejects_malformed_input(value: str) -> None:
    with pytest.raises(ValidationError):
        parse_bbox(value)
