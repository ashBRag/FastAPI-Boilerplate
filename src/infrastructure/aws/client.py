"""AWS client factory with LocalStack support.

Uses aioboto3 for async clients. Clients are created per-request
via Depends() — boto3/aioboto3 clients are not thread-safe for
sharing across requests.

Supported services: s3, sqs, sns. Extend _ENDPOINT_MAP for others.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Literal

import aioboto3

from ..config.settings import settings

logger = logging.getLogger(__name__)

AWSService = Literal["s3", "sqs", "sns"]

_ENDPOINT_MAP: dict[str, str | None] = {
    "s3": settings.AWS_S3_ENDPOINT_URL or settings.AWS_ENDPOINT_URL,
    "sqs": settings.AWS_SQS_ENDPOINT_URL or settings.AWS_ENDPOINT_URL,
    "sns": settings.AWS_SNS_ENDPOINT_URL or settings.AWS_ENDPOINT_URL,
}

_session = aioboto3.Session()


def _client_kwargs(service: str) -> dict[str, Any]:
    """Build kwargs for aioboto3 client creation."""
    kwargs: dict[str, Any] = {"region_name": settings.AWS_REGION}

    endpoint = _ENDPOINT_MAP.get(service)
    if endpoint:
        kwargs["endpoint_url"] = endpoint

    if settings.AWS_ACCESS_KEY_ID:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID

    if settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

    return kwargs


def get_aws_client(service: AWSService):
    """Return a FastAPI dependency that yields an async AWS service client.

    Handles client lifecycle (open/close) per request. LocalStack
    endpoint is used automatically when AWS_ENDPOINT_URL is set.

    Args:
        service: AWS service name — "s3", "sqs", or "sns".

    Usage:
        ```python
        from fastapi import Depends
        from infrastructure.aws.client import get_aws_client

        @router.post("/upload")
        async def upload(s3=Depends(get_aws_client("s3"))):
            await s3.put_object(Bucket="my-bucket", Key="file.txt", Body=b"hello")

        @router.post("/notify")
        async def notify(sns=Depends(get_aws_client("sns"))):
            await sns.publish(TopicArn="arn:aws:sns:...", Message="hello")
        ```

    Raises:
        RuntimeError: If AWS is not enabled in settings.
    """
    async def _dep() -> AsyncGenerator[Any, None]:
        if not settings.AWS_ENABLED:
            raise RuntimeError(
                "AWS is not enabled. Set AWS_ENABLED=true in your environment."
            )

        kwargs = _client_kwargs(service)

        async with _session.client(service, **kwargs) as client:
            logger.debug(f"AWS {service} client opened.")
            yield client
            logger.debug(f"AWS {service} client closed.")

    return _dep