import uuid
from datetime import datetime
from typing import Any


def build_raw_object_key(source_id: uuid.UUID, **kwargs: Any) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return f"raw/{source_id}/{today}/{uuid.uuid4()}.html"


def build_imagery_object_key(content_hash: str, **kwargs: Any) -> str:
    return f"imagery/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}.jpg"


class ObjectStorage:
    async def ensure_bucket(self) -> None:
        pass

    async def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        pass

    async def get_bytes(self, key: str) -> bytes:
        return b""
