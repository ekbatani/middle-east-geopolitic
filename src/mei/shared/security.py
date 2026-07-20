import secrets
from datetime import timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from mei.shared.time import utcnow

_hasher = PasswordHasher()

API_KEY_PREFIX = "mei_"


def generate_api_key() -> str:
    """Generate a new plaintext API key. Only the hash is ever persisted."""
    return API_KEY_PREFIX + secrets.token_urlsafe(32)


def hash_api_key(plaintext_key: str) -> str:
    return _hasher.hash(plaintext_key)


def verify_api_key(plaintext_key: str, key_hash: str) -> bool:
    try:
        return _hasher.verify(key_hash, plaintext_key)
    except VerifyMismatchError:
        return False


def encode_access_token(
    *,
    subject: str,
    scopes: list[str],
    secret_key: str,
    issuer: str,
    audience: str,
    ttl_seconds: int,
) -> str:
    now = utcnow()
    payload: dict[str, Any] = {
        "sub": subject,
        "scopes": scopes,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_access_token(
    token: str,
    *,
    secret_key: str,
    issuer: str,
    audience: str,
) -> dict[str, Any]:
    return jwt.decode(
        token,
        secret_key,
        algorithms=["HS256"],
        issuer=issuer,
        audience=audience,
    )
