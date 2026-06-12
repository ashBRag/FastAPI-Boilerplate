from pydantic_settings import BaseSettings

from ..config.loader import config


class VaultSettings(BaseSettings):
    """HashiCorp Vault settings for API secret management."""

    VAULT_ENABLED: bool = config("VAULT_ENABLED", default=False, cast=bool)
    VAULT_ADDR: str = config("VAULT_ADDR", default="http://localhost:8200")
    VAULT_TOKEN: str | None = config("VAULT_TOKEN", default=None)
    VAULT_MOUNT: str = config("VAULT_MOUNT", default="secret")
    VAULT_NAMESPACE: str | None = config("VAULT_NAMESPACE", default=None)

    # Token renewal
    VAULT_TOKEN_RENEWAL_ENABLED: bool = config("VAULT_TOKEN_RENEWAL_ENABLED", default=True, cast=bool)
    VAULT_TOKEN_RENEWAL_THRESHOLD: int = config("VAULT_TOKEN_RENEWAL_THRESHOLD", default=300, cast=int)  # seconds before expiry

    # Cache fetched secrets in-process to avoid repeated Vault calls
    VAULT_SECRET_CACHE_TTL: int = config("VAULT_SECRET_CACHE_TTL", default=300, cast=int)  # seconds