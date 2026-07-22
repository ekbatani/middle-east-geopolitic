from apps.worker.tasks.dispatch_notifications import evaluate_threshold


def test_evaluate_threshold_greater_than() -> None:
    assert evaluate_threshold(75, ">", 70) is True
    assert evaluate_threshold(65, ">", 70) is False


def test_evaluate_threshold_greater_than_or_equal() -> None:
    assert evaluate_threshold(70, ">=", 70) is True
    assert evaluate_threshold(69.9, ">=", 70) is False


def test_evaluate_threshold_less_than_and_less_than_or_equal() -> None:
    assert evaluate_threshold(10, "<", 20) is True
    assert evaluate_threshold(20, "<=", 20) is True
    assert evaluate_threshold(21, "<=", 20) is False


def test_evaluate_threshold_equality() -> None:
    assert evaluate_threshold(50, "==", 50) is True
    assert evaluate_threshold(50, "==", 51) is False


def test_evaluate_threshold_handles_string_numeric_values() -> None:
    assert evaluate_threshold("82", ">=", "80") is True


def test_evaluate_threshold_non_numeric_input_is_false_not_an_exception() -> None:
    assert evaluate_threshold("not-a-number", ">=", 80) is False
    assert evaluate_threshold(None, ">=", 80) is False


def test_evaluate_threshold_unknown_operator_is_false() -> None:
    assert evaluate_threshold(100, "!=", 80) is False
