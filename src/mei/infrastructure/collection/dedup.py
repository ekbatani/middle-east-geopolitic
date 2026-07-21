import hashlib
import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_FINGERPRINT_BITS = 64
_SHINGLE_SIZE = 4


def _normalize_tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _shingles(tokens: list[str], *, size: int = _SHINGLE_SIZE) -> list[str]:
    if len(tokens) < size:
        return [" ".join(tokens)] if tokens else []
    return [" ".join(tokens[i : i + size]) for i in range(len(tokens) - size + 1)]


def _hash_shingle(shingle: str) -> int:
    digest = hashlib.sha256(shingle.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def compute_fingerprint(text: str) -> str:
    """64-bit simhash of normalized text, for dedup stage 4 (design doc section 11).

    Intentionally exact-match only (no Hamming-distance search) for Phase 2:
    it catches word-for-word republication (wire-service syndication,
    mirrored articles) cheaply. Near-duplicates with substantive edits are
    left to a future semantic-similarity stage rather than approximated here.
    """
    tokens = _normalize_tokens(text)
    shingles = _shingles(tokens)
    if not shingles:
        return "0" * (_FINGERPRINT_BITS // 4)

    weights = [0] * _FINGERPRINT_BITS
    for shingle in shingles:
        shingle_hash = _hash_shingle(shingle)
        for bit in range(_FINGERPRINT_BITS):
            weights[bit] += 1 if (shingle_hash >> bit) & 1 else -1

    fingerprint = 0
    for bit in range(_FINGERPRINT_BITS):
        if weights[bit] > 0:
            fingerprint |= 1 << bit

    return f"{fingerprint:016x}"


__all__ = ["compute_fingerprint"]
