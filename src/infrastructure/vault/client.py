"""Vault client for API secret management.

Only covers KV v2 secrets engine. Token auth only.
Secrets are cached in-process for VAULT_SECRET_CACHE_TTL seconds
to avoid hammering Vault on every request.
"""

import logging
import time
from typing import Any

import hvac

from ..config.settings import settings

logger = logging.getLogger(__name__)

# In-process cache: { "mount/path#key": (value, expires_at) }
_cache: dict[str, tuple[Any, float]] = {}
_client: hvac.Client | None = None


def _get_client() -> hvac.Client:
    """Return authenticated Vault client, initializing if needed.

    Raises:
        RuntimeError: If Vault is disabled or token is missing.
    """
    global _client

    if not settings.VAULT_ENABLED:
        raise RuntimeError("Vault is not enabled. Set VAULT_ENABLED=true in your environment.")

    if not settings.VAULT_TOKEN:
        raise RuntimeError("VAULT_TOKEN is required when Vault is enabled.")

    if _client is None:
        kwargs: dict[str, Any] = {
            "url": settings.VAULT_ADDR,
            "token": settings.VAULT_TOKEN,
        }
        if settings.VAULT_NAMESPACE:
            kwargs["namespace"] = settings.VAULT_NAMESPACE

        _client = hvac.Client(**kwargs)

        if not _client.is_authenticated():
            raise RuntimeError(f"Vault authentication failed. Check VAULT_TOKEN and VAULT_ADDR ({settings.VAULT_ADDR}).")

        logger.info(f"Vault client initialized: {settings.VAULT_ADDR}")

    return _client


def _cache_key(path: str, key: str) -> str:
    return f"{settings.VAULT_MOUNT}/{path}#{key}"


def _read_secret_from_vault(path: str, key: str) -> Any:
    """Fetch a single key from a KV v2 secret path."""
    client = _get_client()

    try:
        response = client.secrets.kv.v2.read_secret_version(
            path=path,
            mount_point=settings.VAULT_MOUNT,
            raise_on_deleted_version=True,
        )
    except hvac.exceptions.InvalidPath:
        raise KeyError(f"Vault secret not found: mount={settings.VAULT_MOUNT} path={path}")

    data: dict[str, Any] = response["data"]["data"]

    if key not in data:
        raise KeyError(f"Key '{key}' not found in Vault secret at path '{path}'.")

    return data[key]


def get_secret(path: str, key: str) -> Any:
    """Fetch a secret from Vault with in-process caching.

    Falls back to env var `{KEY}` if Vault is disabled, allowing
    local dev without a running Vault instance.

    Args:
        path: KV v2 secret path (e.g. "stripe", "sendgrid/prod").
        key: Key within the secret (e.g. "api_key").

    Returns:
        The secret value.

    Raises:
        RuntimeError: If Vault is enabled but unreachable/misconfigured.
        KeyError: If the path or key does not exist in Vault.

    Usage as FastAPI dependency:
        ```python
        from fastapi import Depends

        @router.post("/charge")
        async def charge(
            stripe_key: str = Depends(get_secret_dep("stripe", "api_key"))
        ):
            ...
        ```
    """
    if not settings.VAULT_ENABLED:
        import os
        env_val = os.getenv(key.upper())
        if env_val is None:
            raise KeyError(
                f"Vault is disabled and env var '{key.upper()}' is not set. "
                "Set VAULT_ENABLED=true or provide the env var directly."
            )
        return env_val

    ck = _cache_key(path, key)
    cached_val, expires_at = _cache.get(ck, (None, 0.0))

    if cached_val is not None and time.monotonic() < expires_at:
        return cached_val

    value = _read_secret_from_vault(path, key)
    _cache[ck] = (value, time.monotonic() + settings.VAULT_SECRET_CACHE_TTL)
    logger.debug(f"Fetched secret from Vault: path={path} key={key}")

    return value


def get_secret_dep(path: str, key: str):
    """Return a FastAPI dependency that resolves a Vault secret.

    Usage:
        ```python
        from fastapi import Depends
        from infrastructure.vault.client import get_secret_dep

        @router.post("/charge")
        async def charge(
            stripe_key: str = Depends(get_secret_dep("stripe", "api_key"))
        ):
            client = stripe.Client(api_key=stripe_key)
            ...
        ```
    """
    def _dep() -> Any:
        return get_secret(path, key)

    return _dep


def invalidate_cache(path: str | None = None, key: str | None = None) -> None:
    """Invalidate the in-process secret cache.

    Args:
        path: If provided with key, invalidates only that entry.
        key: If provided with path, invalidates only that entry.
             If neither provided, clears the entire cache.
    """
    global _cache

    if path and key:
        _cache.pop(_cache_key(path, key), None)
    else:
        _cache.clear()
        logger.debug("Vault secret cache cleared.")