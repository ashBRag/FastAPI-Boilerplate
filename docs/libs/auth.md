# libs/auth

A single JWT-verification helper. Takes the secret/algorithm as arguments
instead of importing project config, so it stays reusable as-is.

## Usage

```python
from fastapi import Depends, Header
from libs.auth import verify_token
from libs.errors import UnauthorizedError
from app.core.config import settings

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing bearer token")

    token = authorization.removeprefix("Bearer ")
    payload = verify_token(token, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)

    if payload is None:
        raise UnauthorizedError("Invalid or expired token")

    return payload  # e.g. {"sub": "user-123", "exp": ...}


@app.get("/me")
async def read_me(user: dict = Depends(get_current_user)):
    return {"user_id": user["sub"]}
```

## Behavior

- Returns the decoded claims dict on success.
- Returns `None` (doesn't raise) if the token is invalid, expired, or
  tampered with - the caller decides how to respond (typically a 401 via
  `libs.errors.UnauthorizedError`).
- Raises `ValueError` only for a caller bug - passing a non-string or empty
  token - not for anything token-content-related.

```python
from libs.auth import verify_token

payload = verify_token("eyJhbGciOi...", secret_key="my-secret", algorithm="HS256")
if payload:
    print(payload["sub"])
```
