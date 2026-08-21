# libs/sanitization

Pure functions to clean untrusted input before storing or echoing it back -
HTML-escaping, null-byte stripping, and email format validation. No
framework or settings dependency.

## Usage

```python
from libs.sanitization import sanitize_string, sanitize_email, sanitize_dict, sanitize_list

sanitize_string("<script>alert(1)</script>Hello")
# -> "Hello"   (script tag stripped after escaping)

sanitize_email("  User@Example.COM  ")
# -> "user@example.com"

sanitize_email("not-an-email")
# -> raises ValueError("Invalid email format")
```

Recursive helpers for nested request payloads:

```python
sanitize_dict({
    "name": "<b>Bob</b>",
    "tags": ["<i>vip</i>", "new"],
    "address": {"city": "New\0York"},
})
# -> {
#     "name": "&lt;b&gt;Bob&lt;/b&gt;",
#     "tags": ["&lt;i&gt;vip&lt;/i&gt;", "new"],
#     "address": {"city": "NewYork"},
# }
```

## Typical usage in a route

```python
from fastapi import Body
from libs.sanitization import sanitize_dict

@app.post("/comments")
async def create_comment(payload: dict = Body(...)):
    clean = sanitize_dict(payload)
    return await comments_service.create(clean)
```

Prefer pydantic schema validation for structure/type checks; use these
helpers specifically for cleaning free-text string fields that get stored or
rendered back to other users (comments, bios, titles, etc.).
