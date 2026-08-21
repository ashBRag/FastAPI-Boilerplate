"""Reusable streaming response helpers: Server-Sent Events + NDJSON/text chunks.

Generic and reusable: takes plain async iterators / dataclasses as input,
no dependency on any project's settings, models, or business logic.

SSE usage:

    from libs.streaming import SseEvent, sse_response

    async def event_source():
        yield SseEvent(data="hello")
        yield SseEvent(event="progress", data='{"percent": 50}')
        yield SseEvent(event="done", data="{}")

    @app.get("/stream")
    async def stream(request: Request):
        return sse_response(event_source(), request=request)

NDJSON usage (e.g. progressively streaming LLM tokens or export rows):

    from libs.streaming import ndjson_response

    async def rows():
        async for row in fetch_rows():
            yield {"id": row.id, "name": row.name}

    @app.get("/export")
    async def export():
        return ndjson_response(rows())
"""

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from starlette.requests import Request
from starlette.responses import StreamingResponse

# SSE headers that prevent proxies/load balancers from buffering the stream
# (which would turn a "live" stream into one big delayed chunk).
_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # disables nginx's response buffering specifically
}


@dataclass
class SseEvent:
    """One Server-Sent Event.

    Only `data` is required. Set `event` to let clients dispatch on event
    type (`EventSource.addEventListener(event, ...)`); set `id` so a
    reconnecting client can resume via the `Last-Event-ID` header; set
    `retry` to control the client's reconnect delay (milliseconds).
    """

    data: str
    event: str | None = None
    id: str | None = None
    retry: int | None = None

    def encode(self) -> str:
        """Render this event in the `text/event-stream` wire format.

        Each field becomes its own `field: value` line; multi-line `data`
        is split into repeated `data:` lines per the SSE spec. The blank
        line at the end terminates the event.
        """
        lines: list[str] = []
        if self.id is not None:
            lines.append(f"id: {self.id}")
        if self.event is not None:
            lines.append(f"event: {self.event}")
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        for data_line in self.data.splitlines() or [""]:
            lines.append(f"data: {data_line}")
        return "\n".join(lines) + "\n\n"


async def _sse_byte_stream(
    events: AsyncIterator[SseEvent],
    request: Request | None,
    heartbeat_seconds: float | None,
) -> AsyncIterator[bytes]:
    r"""Encode events to bytes, interleaving heartbeat comments and watching for disconnects.

    A heartbeat is a comment line (`: ping\n\n`) - valid SSE but ignored by
    clients - sent whenever `heartbeat_seconds` elapses without a real event,
    so idle proxies/load balancers don't time out and close the connection.

    Uses a background task for `__anext__()` rather than `asyncio.wait_for`
    directly on it: wait_for cancels its awaitable on timeout, and cancelling
    an async generator's `__anext__()` mid-flight closes the generator for
    good (subsequent calls raise StopAsyncIteration immediately) - a separate
    task can be left running and simply awaited again next loop iteration.
    """
    events_iter = events.__aiter__()
    pending_next: asyncio.Task | None = None

    try:
        while True:
            if request is not None and await request.is_disconnected():
                break

            if pending_next is None:
                pending_next = asyncio.ensure_future(events_iter.__anext__())

            if heartbeat_seconds is not None:
                done, _ = await asyncio.wait({pending_next}, timeout=heartbeat_seconds)
                if not done:
                    yield b": ping\n\n"
                    continue
            else:
                await asyncio.wait({pending_next})

            next_task, pending_next = pending_next, None
            try:
                event = next_task.result()
            except StopAsyncIteration:
                break

            yield event.encode().encode("utf-8")
    finally:
        if pending_next is not None:
            pending_next.cancel()


def sse_response(
    events: AsyncIterator[SseEvent],
    request: Request | None = None,
    heartbeat_seconds: float | None = 15.0,
) -> StreamingResponse:
    """Wrap an async iterator of SseEvent as a `text/event-stream` response.

    Args:
        events: Async generator/iterator yielding SseEvent instances.
        request: Pass the route's Request to stop producing events as soon
            as the client disconnects (checked via `request.is_disconnected()`).
        heartbeat_seconds: Interval for keep-alive comments when no real event
            has been sent; set to None to disable heartbeats entirely.

    Returns:
        StreamingResponse configured with SSE media type and anti-buffering headers.
    """
    return StreamingResponse(
        _sse_byte_stream(events, request, heartbeat_seconds),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


async def _ndjson_byte_stream(items: AsyncIterator[Any]) -> AsyncIterator[bytes]:
    """Serialize each item to one JSON line (newline-delimited JSON)."""
    async for item in items:
        yield (json.dumps(item) + "\n").encode("utf-8")


def ndjson_response(items: AsyncIterator[Any], status_code: int = 200) -> StreamingResponse:
    """Wrap an async iterator of JSON-serializable items as newline-delimited JSON.

    Useful for progressively streaming large result sets/exports without
    buffering the whole payload in memory, and for clients that consume NDJSON
    directly rather than parsing SSE framing.

    Args:
        items: Async generator/iterator yielding JSON-serializable values.
        status_code: HTTP status for the response.
    """
    return StreamingResponse(
        _ndjson_byte_stream(items),
        media_type="application/x-ndjson",
        status_code=status_code,
    )


def text_chunk_response(chunks: AsyncIterator[str], media_type: str = "text/plain") -> StreamingResponse:
    """Wrap an async iterator of text chunks as a plain chunked response.

    For cases that are neither SSE nor NDJSON - e.g. streaming raw LLM
    completion text straight through to the client as it's generated.
    """

    async def _byte_stream() -> AsyncIterator[bytes]:
        async for chunk in chunks:
            yield chunk.encode("utf-8")

    return StreamingResponse(_byte_stream(), media_type=media_type)
