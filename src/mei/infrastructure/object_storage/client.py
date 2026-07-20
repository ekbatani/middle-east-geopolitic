import asyncio
from datetime import datetime
from functools import lru_cache
from uuid import UUID

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError

from mei.shared.config import get_settings


@lru_cache
def _get_boto_client() -> BaseClient:
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def build_raw_object_key(
    *,
    source_id: UUID,
    document_id: UUID,
    content_hash: str,
    extension: str,
    retrieved_at: datetime,
) -> str:
    """Object key layout from design doc section 10.4.

    raw/{yyyy}/{mm}/{dd}/{source_id}/{document_id}-{sha256}.{ext}
    """
    return f"raw/{retrieved_at:%Y/%m/%d}/{source_id}/{document_id}-{content_hash}.{extension}"


class ObjectStorage:
    """Thin async wrapper around the S3-compatible (MinIO) client.

    boto3 is synchronous; every call is pushed to a worker thread so it
    doesn't block the event loop.
    """

    def __init__(self, bucket: str | None = None) -> None:
        settings = get_settings()
        self._bucket = bucket or settings.s3_bucket
        self._client = _get_boto_client()

    async def ensure_bucket(self) -> None:
        await asyncio.to_thread(self._ensure_bucket_sync)

    def _ensure_bucket_sync(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self._bucket)

    async def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type or "application/octet-stream",
        )

    async def get_bytes(self, key: str) -> bytes:
        response = await asyncio.to_thread(self._client.get_object, Bucket=self._bucket, Key=key)
        body: bytes = response["Body"].read()
        return body


__all__ = ["ObjectStorage", "build_raw_object_key"]
