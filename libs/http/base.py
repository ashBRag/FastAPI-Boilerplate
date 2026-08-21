"""Reusable async HTTP client factory: sane timeouts + retry/backoff + logging.

Self-contained: takes a logger-like object as a parameter instead of
importing libs.logging, so it stays independently reusable/extractable.

Usage:

    from libs.http import build_http_client

    client = build_http_client(base_url="https://api.example.com", logger=logger)
    response = await client.get("/things/123")   # retries on network errors / 5xx
    await client.aclose()

Or as an async context manager:

    async with build_http_client() as client:
        response = await client.get("https://example.com")
"""

from typing import Any, Protocol

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

# Retry on connection-level failures and server errors (5xx), but never on
# 4xx - a bad request won't succeed just because we send it again.
_RETRYABLE_STATUS_CODES = {500, 502, 503, 504}


class _Logger(Protocol):
    """Structural type for whatever logger build_http_client() is given."""

    def warning(self, event: str, **kwargs: Any) -> None: ...


def _is_retryable(exc: BaseException) -> bool:
    """True for connection/timeout errors and 5xx responses; False otherwise."""
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _RETRYABLE_STATUS_CODES
    return False


def _raise_for_retryable_status(response: httpx.Response) -> httpx.Response:
    """Raise on 5xx so tenacity's retry wrapper can catch and retry it.

    4xx is intentionally left alone: callers should handle "not found",
    "unauthorized", etc. themselves via response.raise_for_status() or
    response.status_code checks - retrying those would just waste calls.
    """
    if response.status_code in _RETRYABLE_STATUS_CODES:
        response.raise_for_status()
    return response


def build_http_client(
    base_url: str = "",
    timeout: float = 10.0,
    max_attempts: int = 3,
    logger: _Logger | None = None,
    **client_kwargs: Any,
) -> httpx.AsyncClient:
    """Build an httpx.AsyncClient with retry/backoff wired in via an event hook.

    Args:
        base_url: Optional base URL so callers can pass just the path.
        timeout: Per-request timeout in seconds, applied to connect/read/write/pool.
        max_attempts: Total attempts (including the first) before giving up.
        logger: Optional logger; a warning is emitted before each retry.
        **client_kwargs: Passed straight through to httpx.AsyncClient (headers, auth, etc).

    Returns:
        httpx.AsyncClient: ready to use; caller is responsible for calling
        `.aclose()` (or using it as an async context manager).
    """

    def _log_retry(retry_state) -> None:
        if logger is not None:
            logger.warning(
                "http_request_retry",
                attempt=retry_state.attempt_number,
                exception=str(retry_state.outcome.exception()),
            )

    retrying_get = retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=0.5, max=5),
        retry=retry_if_exception(_is_retryable),
        before_sleep=_log_retry,
    )

    client = httpx.AsyncClient(base_url=base_url, timeout=timeout, **client_kwargs)

    # Wrap client.send with retry logic. httpx doesn't have a native retry
    # hook, so we patch the bound method rather than subclassing - keeps this
    # a one-function factory instead of a whole AsyncClient subclass.
    original_send = client.send

    @retrying_get
    async def _send_with_retry(*args: Any, **kwargs: Any) -> httpx.Response:
        response = await original_send(*args, **kwargs)
        return _raise_for_retryable_status(response)

    client.send = _send_with_retry  # type: ignore[method-assign]

    return client
