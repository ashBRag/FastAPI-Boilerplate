# libs/streaming

Streaming response helpers: Server-Sent Events (SSE), NDJSON, and raw text
chunking. Built on Starlette's `StreamingResponse` - no extra dependency
needed for SSE.

## SSE usage

```python
from fastapi import Request
from libs.streaming import SseEvent, sse_response

@app.get("/stream")
async def stream(request: Request):
    async def events():
        yield SseEvent(data="connected")
        for i in range(10):
            yield SseEvent(event="progress", data=str(i), id=str(i))
        yield SseEvent(event="done", data="{}")

    return sse_response(events(), request=request)
```

Pass `request` so the generator stops producing events as soon as the client
disconnects (checked via `request.is_disconnected()`), instead of running to
completion against a dead connection.

### Heartbeats

By default, a `: ping\n\n` comment line is sent every 15 seconds of silence
so idle proxies/load balancers don't close the connection. Tune or disable it:

```python
sse_response(events(), request=request, heartbeat_seconds=30.0)
sse_response(events(), request=request, heartbeat_seconds=None)  # disabled
```

### Client-side (browser)

```javascript
const source = new EventSource("/stream");
source.addEventListener("progress", (e) => console.log("progress:", e.data));
source.addEventListener("done", () => source.close());
```

## NDJSON usage

For progressively streaming large result sets without buffering the whole
response in memory:

```python
from libs.streaming import ndjson_response

@app.get("/export")
async def export():
    async def rows():
        async for row in fetch_all_rows():  # some async generator over your data
            yield {"id": row.id, "name": row.name}

    return ndjson_response(rows())
```

Each item is serialized as one JSON object per line
(`application/x-ndjson`) - simpler for clients that just want to parse line
by line, without SSE's `data:`/`event:` framing.

## Raw text chunk usage

For streaming plain text as it's generated - e.g. LLM completion tokens
straight through to the client:

```python
from libs.streaming import text_chunk_response

@app.get("/complete")
async def complete(prompt: str):
    async def tokens():
        async for token in llm_client.stream(prompt):
            yield token

    return text_chunk_response(tokens())
```

## SseEvent fields

```python
SseEvent(
    data="payload",       # required; multi-line strings become multiple `data:` lines
    event="progress",      # optional; lets clients dispatch via addEventListener(event, ...)
    id="42",               # optional; sent back as Last-Event-ID on client reconnect
    retry=3000,            # optional; client's reconnect delay in milliseconds
)
```
