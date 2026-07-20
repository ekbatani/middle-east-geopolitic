from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def ensure_aware_utc(value: datetime) -> datetime:
    """Require a timezone-aware datetime and normalize it to UTC.

    Timestamps in this platform must always carry timezone info; naive
    datetimes are a common source of silent off-by-hours errors when
    comparing source-published times across languages and locales.
    """
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(UTC)
