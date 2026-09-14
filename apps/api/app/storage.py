import io
import uuid

from minio import Minio

from app.config import settings

_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


def ensure_bucket() -> None:
    if not _client.bucket_exists(settings.minio_bucket):
        _client.make_bucket(settings.minio_bucket)


def put_asset(data: bytes, content_type: str) -> str:
    object_key = f"decks/{uuid.uuid4()}"
    _client.put_object(
        settings.minio_bucket,
        object_key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return object_key


def presigned_get_url(object_key: str) -> str:
    return _client.presigned_get_object(settings.minio_bucket, object_key)
