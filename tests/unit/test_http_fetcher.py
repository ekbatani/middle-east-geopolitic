import socket

import pytest

from mei.infrastructure.collection.http_fetcher import validate_url_security
from mei.shared.errors import UnsupportedURLError


def test_rejects_disallowed_scheme() -> None:
    with pytest.raises(UnsupportedURLError):
        validate_url_security("ftp://example.com/file.txt")


def test_rejects_missing_hostname() -> None:
    with pytest.raises(UnsupportedURLError):
        validate_url_security("http:///path-only")


def test_rejects_loopback_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, None, None, None, ("127.0.0.1", 0))],
    )

    with pytest.raises(UnsupportedURLError):
        validate_url_security("http://internal.example/")


def test_rejects_private_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, None, None, None, ("10.0.0.5", 0))],
    )

    with pytest.raises(UnsupportedURLError):
        validate_url_security("http://internal.example/")


def test_rejects_link_local_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, None, None, None, ("169.254.169.254", 0))],
    )

    with pytest.raises(UnsupportedURLError):
        validate_url_security("http://metadata.internal/")


def test_allows_public_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, None, None, None, ("93.184.216.34", 0))],
    )

    validate_url_security("https://example.com/article")


def test_rejects_unresolvable_host(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_args: object, **_kwargs: object) -> None:
        raise socket.gaierror("name resolution failed")

    monkeypatch.setattr(socket, "getaddrinfo", _raise)

    with pytest.raises(UnsupportedURLError):
        validate_url_security("http://does-not-resolve.invalid/")
