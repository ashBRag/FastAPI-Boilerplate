"""Tests for the rate limiter middleware module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response

from src.infrastructure.rate_limit.exceptions import RateLimitException
from src.infrastructure.rate_limit.middleware import (
    RateLimiterMiddleware,
    _check_rate_limit,
)


@pytest.fixture
def mock_request():
    mock = MagicMock(spec=Request)
    mock.url = MagicMock()
    mock.url.path = "/api/v1/test"
    mock.client = MagicMock()
    mock.client.host = "127.0.0.1"
    mock.state = MagicMock()
    mock.app = MagicMock()
    mock.app.state = MagicMock()
    mock.app.state.initialization_complete = AsyncMock()
    mock.app.state.initialization_complete.wait = AsyncMock()
    return mock


@pytest.fixture
def mock_response():
    mock = MagicMock(spec=Response)
    mock.headers = {}
    return mock


@pytest.fixture
def mock_app():
    return MagicMock()


@pytest.mark.asyncio
async def test_check_rate_limit_disabled(mock_request):
    with patch("src.infrastructure.rate_limit.middleware.settings") as mock_settings:
        mock_settings.RATE_LIMITER_ENABLED = False
        await _check_rate_limit(mock_request)


@pytest.mark.asyncio
async def test_check_rate_limit_by_ip(mock_request):
    with (
        patch("src.infrastructure.rate_limit.middleware.settings") as mock_settings,
        patch("src.infrastructure.rate_limit.middleware.DEFAULT_LIMIT", 100),
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_increment,
    ):
        mock_settings.RATE_LIMITER_ENABLED = True
        mock_settings.DEFAULT_RATE_LIMIT_LIMIT = 100
        mock_settings.DEFAULT_RATE_LIMIT_PERIOD = 60
        mock_settings.RATE_LIMITER_FAIL_OPEN = True
        mock_increment.return_value = (1, False)

        await _check_rate_limit(mock_request)

        mock_increment.assert_called_once()
        key_arg = mock_increment.call_args.kwargs["key"]
        assert "127.0.0.1" in key_arg
        assert mock_increment.call_args.kwargs["limit"] == 100
        assert mock_increment.call_args.kwargs["period"] == 60


@pytest.mark.asyncio
async def test_check_rate_limit_exceeded(mock_request):
    with (
        patch("src.infrastructure.rate_limit.middleware.settings") as mock_settings,
        patch("src.infrastructure.rate_limit.middleware.DEFAULT_LIMIT", 100),
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_increment,
        patch("src.infrastructure.rate_limit.middleware.logger") as mock_logger,
    ):
        mock_settings.RATE_LIMITER_ENABLED = True
        mock_settings.DEFAULT_RATE_LIMIT_LIMIT = 100
        mock_settings.DEFAULT_RATE_LIMIT_PERIOD = 60
        mock_settings.RATE_LIMITER_FAIL_OPEN = True
        mock_increment.return_value = (101, True)

        with pytest.raises(RateLimitException) as excinfo:
            await _check_rate_limit(mock_request)

        assert "Rate limit exceeded" in str(excinfo.value)
        assert mock_logger.warning.called


@pytest.mark.asyncio
async def test_check_rate_limit_fail_closed_on_error(mock_request):
    with (
        patch("src.infrastructure.rate_limit.middleware.settings") as mock_settings,
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_increment,
    ):
        mock_settings.RATE_LIMITER_ENABLED = True
        mock_settings.DEFAULT_RATE_LIMIT_LIMIT = 100
        mock_settings.DEFAULT_RATE_LIMIT_PERIOD = 60
        mock_settings.RATE_LIMITER_FAIL_OPEN = False
        mock_increment.side_effect = Exception("Redis down")

        with pytest.raises(RateLimitException):
            await _check_rate_limit(mock_request)


@pytest.mark.asyncio
async def test_check_rate_limit_fail_open_on_error(mock_request):
    with (
        patch("src.infrastructure.rate_limit.middleware.settings") as mock_settings,
        patch("src.infrastructure.rate_limit.middleware.increment_and_check") as mock_increment,
    ):
        mock_settings.RATE_LIMITER_ENABLED = True
        mock_settings.DEFAULT_RATE_LIMIT_LIMIT = 100
        mock_settings.DEFAULT_RATE_LIMIT_PERIOD = 60
        mock_settings.RATE_LIMITER_FAIL_OPEN = True
        mock_increment.side_effect = Exception("Redis down")

        # should not raise
        await _check_rate_limit(mock_request)


@pytest.mark.asyncio
async def test_rate_limiter_middleware_sets_headers(mock_request, mock_response, mock_app):
    middleware = RateLimiterMiddleware(app=mock_app)

    async def next_handler(request):
        return mock_response

    with patch("src.infrastructure.rate_limit.middleware._check_rate_limit", new_callable=AsyncMock):
        mock_request.state.rate_limit_headers = {
            "X-RateLimit-Limit": "10",
            "X-RateLimit-Remaining": "5",
            "X-RateLimit-Reset": "60",
        }

        response = await middleware.dispatch(mock_request, next_handler)

        assert response.headers["X-RateLimit-Limit"] == "10"
        assert response.headers["X-RateLimit-Remaining"] == "5"
        assert response.headers["X-RateLimit-Reset"] == "60"


@pytest.mark.asyncio
async def test_rate_limiter_middleware_no_headers(mock_request, mock_response, mock_app):
    middleware = RateLimiterMiddleware(app=mock_app)

    async def next_handler(request):
        return mock_response

    with patch("src.infrastructure.rate_limit.middleware._check_rate_limit", new_callable=AsyncMock):
        if hasattr(mock_request.state, "rate_limit_headers"):
            delattr(mock_request.state, "rate_limit_headers")

        response = await middleware.dispatch(mock_request, next_handler)

        assert len(response.headers) == 0