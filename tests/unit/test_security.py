import pytest

from mei.shared.security import (
    decode_access_token,
    encode_access_token,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)


def test_api_key_roundtrip() -> None:
    plaintext = generate_api_key()
    key_hash = hash_api_key(plaintext)

    assert verify_api_key(plaintext, key_hash)


def test_api_key_rejects_wrong_key() -> None:
    key_hash = hash_api_key(generate_api_key())

    assert not verify_api_key(generate_api_key(), key_hash)


def test_access_token_roundtrip() -> None:
    token = encode_access_token(
        subject="user-1",
        scopes=["intelligence:read"],
        secret_key="test-secret",
        issuer="mei-platform",
        audience="mei-clients",
        ttl_seconds=60,
    )

    payload = decode_access_token(
        token, secret_key="test-secret", issuer="mei-platform", audience="mei-clients"
    )

    assert payload["sub"] == "user-1"
    assert payload["scopes"] == ["intelligence:read"]


def test_access_token_rejects_wrong_audience() -> None:
    token = encode_access_token(
        subject="user-1",
        scopes=[],
        secret_key="test-secret",
        issuer="mei-platform",
        audience="mei-clients",
        ttl_seconds=60,
    )

    with pytest.raises(Exception):  # noqa: B017 - PyJWTError subclass, any is acceptable here
        decode_access_token(
            token, secret_key="test-secret", issuer="mei-platform", audience="wrong-audience"
        )
