import time

from mei.shared.ids import uuid7


def test_uuid7_has_version_7() -> None:
    generated = uuid7()

    assert generated.version == 7


def test_uuid7_is_unique() -> None:
    generated = {uuid7() for _ in range(1000)}

    assert len(generated) == 1000


def test_uuid7_is_time_ordered() -> None:
    first = uuid7()
    time.sleep(0.002)
    second = uuid7()

    assert str(first) < str(second)
