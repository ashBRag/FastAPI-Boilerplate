"""Async HTTP client factory with default timeouts and retry/backoff.

Self-contained: no dependency on any other libs/* package.
"""

from libs.http.base import build_http_client

__all__ = ["build_http_client"]
