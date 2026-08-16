from pathlib import Path
import yaml
import pytest

from mei.shared.enums import (
    ActorType,
    EndpointType,
    IndicatorDirection,
    IndicatorNormalizationMethod,
    SourceType,
)

CONFIGS_DIR = Path(__file__).resolve().parent.parent.parent / "configs"


def test_actors_seed_enums_valid() -> None:
    path = CONFIGS_DIR / "actors.seed.yml"
    assert path.exists()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    for entry in raw.get("actors", []):
        assert ActorType(entry["actor_type"]) in ActorType


def test_sources_seed_enums_valid() -> None:
    path = CONFIGS_DIR / "source-policy.yml"
    assert path.exists()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    for entry in raw.get("sources", []):
        assert SourceType(entry["source_type"]) in SourceType
        for endpoint in entry.get("endpoints", []):
            if "endpoint_type" in endpoint:
                assert EndpointType(endpoint["endpoint_type"]) in EndpointType


def test_risk_indicators_seed_enums_valid() -> None:
    path = CONFIGS_DIR / "risk-indicators.yml"
    assert path.exists()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    for entry in raw.get("indicators", []):
        assert (
            IndicatorNormalizationMethod(entry["normalization_method"])
            in IndicatorNormalizationMethod
        )

    for entry in raw.get("risk_definitions", []):
        for weight_entry in entry.get("weights", []):
            if "direction" in weight_entry:
                assert IndicatorDirection(weight_entry["direction"]) in IndicatorDirection
