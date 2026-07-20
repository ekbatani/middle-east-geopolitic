from mei.shared.errors import MeiError, NotFoundError


def test_not_found_error_defaults() -> None:
    error = NotFoundError()

    assert error.status_code == 404
    assert error.detail == "Resource Not Found"


def test_error_accepts_custom_detail() -> None:
    error = NotFoundError("actor abc123 not found")

    assert error.detail == "actor abc123 not found"
    assert isinstance(error, MeiError)
