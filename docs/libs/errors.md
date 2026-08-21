# libs/errors

A consistent API error shape for every response - expected (404, 409, ...) or
unexpected (bugs, DB outages):

```json
{"error": {"code": "not_found", "message": "...", "details": {}}}
```

## Setup

```python
# app/main.py
from libs.errors import register_exception_handlers

register_exception_handlers(app, logger=logger, debug=settings.DEBUG)
```

This registers handlers for:
- `AppError` (and subclasses) - your own raised errors
- `HTTPException` (Starlette's base class, so it also catches routing-layer
  404/405, not just explicit raises)
- `RequestValidationError` - pydantic/FastAPI request validation failures
- any other `Exception` - last-resort 500; only echoes the real message back
  to the client when `debug=True`, otherwise says "An unexpected error occurred"

## Usage - raising errors from route/service code

```python
from libs.errors import NotFoundError, ConflictError, ForbiddenError

@app.get("/widgets/{widget_id}")
async def get_widget(widget_id: int):
    widget = await widgets_service.find(widget_id)
    if widget is None:
        raise NotFoundError(f"Widget {widget_id} not found")
    return widget


@app.post("/widgets")
async def create_widget(payload: WidgetCreate):
    if await widgets_service.exists(payload.name):
        raise ConflictError(
            "A widget with this name already exists",
            details={"name": payload.name},
        )
    return await widgets_service.create(payload)


@app.delete("/widgets/{widget_id}")
async def delete_widget(widget_id: int, user: dict = Depends(get_current_user)):
    if not user_can_delete(user, widget_id):
        raise ForbiddenError("You don't have permission to delete this widget")
    await widgets_service.delete(widget_id)
```

## Available error classes

| Class | Status | Use for |
|---|---|---|
| `BadRequestError` | 400 | Malformed input validation didn't catch |
| `UnauthorizedError` | 401 | Missing/invalid credentials |
| `ForbiddenError` | 403 | Valid credentials, insufficient permission |
| `NotFoundError` | 404 | Resource doesn't exist |
| `ConflictError` | 409 | Duplicate / conflicts with current state |
| `AppError` | 500 | Base class - subclass for anything else |

## Custom error types

Subclass `AppError` directly for anything project-specific:

```python
from libs.errors import AppError
from fastapi import status

class PaymentDeclinedError(AppError):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    code = "payment_declined"

raise PaymentDeclinedError("Card was declined", details={"decline_code": "insufficient_funds"})
```

## Example responses

```
GET /widgets/999          -> 404 {"error":{"code":"not_found","message":"Widget 999 not found"}}
GET /does-not-exist       -> 404 {"error":{"code":"http_error","message":"Not Found"}}
POST /widgets (bad body)  -> 422 {"error":{"code":"validation_error","message":"Request validation failed","details":{"errors":[...]}}}
(unhandled bug)           -> 500 {"error":{"code":"internal_error","message":"An unexpected error occurred"}}
```
