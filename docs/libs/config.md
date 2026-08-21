# libs/config

`BaseAppSettings` + `Environment`: environment-aware `.env` file resolution,
plus per-environment defaults (log level, rate limits, ...) that only apply
when the corresponding variable isn't set explicitly.

## Setup

Subclass `BaseAppSettings` in your project's own `core/config.py` and add
whatever fields your project needs:

```python
# app/core/config.py
from libs.config import BaseAppSettings, Environment

class Settings(BaseAppSettings):
    PROJECT_NAME: str = "My Service"
    API_V1_STR: str = "/api/v1"

    # Per-route rate limits; RATE_LIMIT_DEFAULT (from BaseAppSettings) applies
    # to any route not listed here.
    RATE_LIMIT_ENDPOINTS: dict[str, list[str]] = {
        "root": ["60 per minute"],
        "health": ["20 per minute"],
    }

# Construct once, apply environment defaults, and share app-wide.
settings = Settings().apply_environment_defaults()
```

## Usage

```python
from app.core.config import settings

print(settings.ENVIRONMENT)        # Environment.DEVELOPMENT
print(settings.DEBUG)               # True in dev, False in staging/prod (unless DEBUG is set explicitly)
print(settings.RATE_LIMIT_DEFAULT)  # ["1000 per day", "200 per hour"] in dev
```

`.env` file resolution (first match wins, relative to the current working directory):

```
.env.<environment>.local   # e.g. .env.development.local - your own machine-specific overrides
.env.<environment>          # e.g. .env.development - checked in, shared per environment
.env.local
.env
```

## Customizing per-environment defaults

Override `environment_defaults` in your subclass instead of editing `libs/config`:

```python
class Settings(BaseAppSettings):
    environment_defaults = {
        **BaseAppSettings.environment_defaults,
        Environment.PRODUCTION: {
            **BaseAppSettings.environment_defaults[Environment.PRODUCTION],
            "RATE_LIMIT_DEFAULT": ["5000 per day", "500 per hour"],
        },
    }
```
