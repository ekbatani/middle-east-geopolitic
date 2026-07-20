import os
import time
import uuid


def uuid7() -> uuid.UUID:
    """Generate a UUIDv7 (RFC 9562): time-ordered, globally unique.

    Sortable IDs let primary-key order match insertion order, which keeps
    intelligence records' natural chronology intact without a separate
    `created_at` index for range scans.
    """
    unix_ms = time.time_ns() // 1_000_000
    rand = os.urandom(10)

    time_bytes = unix_ms.to_bytes(6, byteorder="big")

    # Set version (7) in the high nibble of byte 6, keep 12 bits of randomness.
    byte6 = (0x70 | (rand[0] & 0x0F)).to_bytes(1, byteorder="big")
    byte7 = rand[1].to_bytes(1, byteorder="big")

    # Set variant (RFC 4122) in the high two bits of byte 8.
    byte8 = (0x80 | (rand[2] & 0x3F)).to_bytes(1, byteorder="big")
    remaining = rand[3:10]

    return uuid.UUID(bytes=time_bytes + byte6 + byte7 + byte8 + remaining)


def new_id() -> str:
    """Return a new UUIDv7 as a string, suitable for use as a primary key."""
    return str(uuid7())
