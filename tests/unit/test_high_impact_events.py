from mei.application.services.events import HIGH_IMPACT_EVENT_TYPES, is_high_impact_event


def test_listed_high_impact_event_type_is_flagged() -> None:
    assert is_high_impact_event("nuclear_incident", None) is True


def test_critical_significance_is_flagged_regardless_of_type() -> None:
    assert is_high_impact_event("routine_protest", "critical") is True


def test_ordinary_event_is_not_flagged() -> None:
    assert is_high_impact_event("routine_protest", "low") is False


def test_every_high_impact_type_is_flagged() -> None:
    for event_type in HIGH_IMPACT_EVENT_TYPES:
        assert is_high_impact_event(event_type, None) is True
