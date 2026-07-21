from mei.application.services.scenario_engine import (
    check_family_consistency,
    normalize_probability_range,
)
from mei.shared.enums import ScenarioFamily


def test_normalize_probability_range_swaps_out_of_order_bounds() -> None:
    assert normalize_probability_range(70.0, 30.0) == (30.0, 70.0)


def test_normalize_probability_range_clamps_to_bounds() -> None:
    assert normalize_probability_range(-10.0, 150.0) == (0.0, 100.0)


def test_normalize_probability_range_leaves_valid_range_untouched() -> None:
    assert normalize_probability_range(20.0, 40.0) == (20.0, 40.0)


def test_family_consistency_flags_more_severe_floor_above_less_severe_ceiling() -> None:
    assessments = {
        ScenarioFamily.CONTROLLED_DEESCALATION: (0.0, 20.0),
        ScenarioFamily.REGIONAL_ESCALATION: (50.0, 80.0),
    }
    warnings = check_family_consistency(assessments)
    assert len(warnings) == 1
    assert "regional_escalation" in warnings[0]
    assert "controlled_deescalation" in warnings[0]


def test_family_consistency_allows_overlapping_ranges() -> None:
    assessments = {
        ScenarioFamily.CONTROLLED_DEESCALATION: (10.0, 60.0),
        ScenarioFamily.MANAGED_CONFRONTATION: (20.0, 70.0),
    }
    assert check_family_consistency(assessments) == []


def test_family_consistency_ignores_families_not_present() -> None:
    assessments = {ScenarioFamily.SYSTEMIC_REGIONAL_WAR: (0.0, 5.0)}
    assert check_family_consistency(assessments) == []


def test_family_consistency_checks_only_adjacent_severity_pairs() -> None:
    # Two non-adjacent families (deescalation and systemic war) with an
    # inverted relationship still get flagged, since the severity ordering
    # is checked pairwise across every consecutive pair actually present.
    assessments = {
        ScenarioFamily.CONTROLLED_DEESCALATION: (0.0, 10.0),
        ScenarioFamily.SYSTEMIC_REGIONAL_WAR: (90.0, 100.0),
    }
    warnings = check_family_consistency(assessments)
    assert len(warnings) == 1
