from pydantic_settings import BaseSettings

from ..config.loader import config


class AWSSettings(BaseSettings):
    """AWS / LocalStack connection settings."""

    AWS_ENABLED: bool = config("AWS_ENABLED", default=False, cast=bool)
    AWS_REGION: str = config("AWS_REGION", default="us-east-1")
    AWS_ACCESS_KEY_ID: str | None = config("AWS_ACCESS_KEY_ID", default=None)
    AWS_SECRET_ACCESS_KEY: str | None = config("AWS_SECRET_ACCESS_KEY", default=None)

    # LocalStack override — set this in dev to point at LocalStack
    AWS_ENDPOINT_URL: str | None = config("AWS_ENDPOINT_URL", default=None)

    # Per-service endpoint overrides (optional, falls back to AWS_ENDPOINT_URL)
    AWS_S3_ENDPOINT_URL: str | None = config("AWS_S3_ENDPOINT_URL", default=None)
    AWS_SQS_ENDPOINT_URL: str | None = config("AWS_SQS_ENDPOINT_URL", default=None)
    AWS_SNS_ENDPOINT_URL: str | None = config("AWS_SNS_ENDPOINT_URL", default=None)