# libs/aws

Async AWS clients for **S3 and SQS only** (`aioboto3`). No connect/disconnect
lifecycle - each call opens a fresh client as an async context manager, which
is aioboto3's own recommended usage (clients are cheap to create, not meant
to be held open indefinitely).

## Setup

```python
from libs.aws import AwsSettings, S3Client, SqsClient

aws_settings = AwsSettings(
    region_name=settings.AWS_REGION,
    # access_key_id / secret_access_key: leave unset to use the default boto3
    # credential chain (env vars, instance profile, ...) - recommended outside
    # of local dev / LocalStack.
)

s3 = S3Client(aws_settings, bucket=settings.S3_BUCKET)
sqs = SqsClient(aws_settings, queue_url=settings.SQS_QUEUE_URL)
```

## S3 usage

```python
# Upload
await s3.upload_bytes("uploads/report.json", b'{"a": 1}', content_type="application/json")

# Download
data = await s3.download_bytes("uploads/report.json")

# Delete
await s3.delete("uploads/report.json")

# Time-limited download link for a client (e.g. a browser)
url = await s3.presigned_url("uploads/report.json", expires_in=600)

# Health check (never raises)
bucket_ok = await s3.health_check()
```

Typical route usage - accept an upload, store it, return a link:

```python
from fastapi import UploadFile

@app.post("/reports")
async def upload_report(file: UploadFile):
    key = f"reports/{file.filename}"
    await s3.upload_bytes(key, await file.read(), content_type=file.content_type)
    return {"url": await s3.presigned_url(key)}
```

## SQS usage

```python
# Send
message_id = await sqs.send_message('{"event": "order_created", "order_id": 42}')

# Receive (long poll for up to 10s to reduce empty responses)
messages = await sqs.receive_messages(max_messages=10, wait_time_seconds=10)
for msg in messages:
    payload = json.loads(msg["Body"])
    await handle_event(payload)
    await sqs.delete_message(msg["ReceiptHandle"])  # only after successful processing

# Health check (never raises)
queue_ok = await sqs.health_check()
```

Typical usage - a polling worker task:

```python
# app/workers/sqs_poller.py
import asyncio
import json

async def run() -> None:
    while True:
        messages = await sqs.receive_messages(max_messages=10, wait_time_seconds=10)
        for msg in messages:
            try:
                await handle_event(json.loads(msg["Body"]))
                await sqs.delete_message(msg["ReceiptHandle"])
            except Exception:
                logger.error("sqs_message_processing_failed", message_id=msg["MessageId"])
                # leave it un-deleted; it'll become visible again after the queue's
                # visibility timeout and can be retried (or land in a DLQ if configured)
```

## Local development with LocalStack

```python
aws_settings = AwsSettings(
    region_name="us-east-1",
    access_key_id="test",
    secret_access_key="test",
    endpoint_url="http://localhost:4566",
)
```
