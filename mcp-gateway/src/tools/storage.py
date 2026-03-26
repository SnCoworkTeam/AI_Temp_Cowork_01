"""
对象存储辅助方法（MinIO）
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional

from minio import Minio

from ..config import settings

logger = logging.getLogger(__name__)


def _build_minio_client() -> Optional[Minio]:
    """构建 MinIO 客户端。如果配置不完整则返回 None。"""
    if not settings.MINIO_ENDPOINT or not settings.MINIO_ACCESS_KEY or not settings.MINIO_SECRET_KEY or not settings.MINIO_BUCKET:
        logger.debug("MinIO config incomplete, skip upload")
        return None

    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
        region=settings.MINIO_REGION,
    )


def _ensure_bucket(client: Minio, bucket: str):
    """确保 bucket 存在，不存在则创建。"""
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except Exception as e:
        logger.warning(f"Failed to ensure bucket '{bucket}': {e}")
        raise


def upload_to_minio(file_path: Path, content_type: Optional[str] = None, prefix: str = "reports") -> Optional[str]:
    """
    上传文件到 MinIO，返回可访问的 URL。
    若配置缺失则返回 None（调用方可使用本地路径）。
    """
    client = _build_minio_client()
    if not client:
        return None

    bucket = settings.MINIO_BUCKET
    _ensure_bucket(client, bucket)

    object_name = f"{prefix}/{uuid.uuid4().hex}/{file_path.name}"
    client.fput_object(bucket, object_name, str(file_path), content_type=content_type)

    scheme = "https" if settings.MINIO_SECURE else "http"
    url = f"{scheme}://{settings.MINIO_ENDPOINT}/{bucket}/{object_name}"
    return url




















