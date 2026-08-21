---
name: libs
description: Use when adding a new package under libs/, or updating/extending an existing one (e.g. libs/db, libs/redis, libs/errors).
---

# Adding or updating a `libs/*` package

`libs/` holds reusable, project-agnostic building blocks - each folder is
self-contained enough to copy into another project, or split into its own
repo, without touching the rest of `libs/` or `app/`.

## Layout convention

Every package is one folder:

```
libs/<name>/
  base.py       # all the actual code
  __init__.py   # thin re-export of the public API from base.py
```

`app/` imports from the folder (`from libs.<name> import X`), never from
`base.py` directly.

## Rules for a new/updated package

1. **No dependency on `app/`.** Never `import app.core.config` or similar
   from inside `libs/`. Anything the package needs (settings values, a
   logger, metric objects) is passed in via constructor/function arguments.

2. **Settings as a plain value object, not `pydantic.BaseSettings`.** If the
   package needs configuration (host, port, credentials, ...), define a
   `@dataclass(frozen=True)` for it (e.g. `DatabaseSettings`, `RedisSettings`,
   `AwsSettings`) - not a `BaseSettings` subclass. This keeps `libs/` free of
   a dependency on `pydantic-settings`/the project's config class; the
   caller in `app/` builds the value object from its own `Settings` instance.
   Exception: `libs/config` itself, whose whole job is the `BaseAppSettings`
   base class - that one *is* pydantic-settings.

3. **Structural typing for cross-cutting dependencies.** If a package needs
   "something logger-shaped" (not a specific logger class), define a
   `Protocol` for it locally rather than importing `libs.logging` or
   `structlog` types. See `libs/errors/base.py`'s `_Logger` Protocol and
   `libs/http/base.py`'s `_Logger` Protocol for the pattern. Only
   `libs/middleware` is allowed to import another `libs/*` package directly
   (`libs.logging`'s `bind_context`/`clear_context`), because that coupling
   is unavoidable for what it does - keep new cross-package imports to a
   similar bar.

4. **Lifecycle methods, when the package holds a persistent connection.**
   For anything that owns a connection/pool (Postgres, Redis, Kafka), follow
   the shape already used by `libs/db`, `libs/redis`, `libs/kafka`:
   - `async def connect(self) -> None` - verify connectivity, fail fast
   - `async def disconnect(self) -> None` - clean shutdown
   - `async def health_check(self) -> bool` - **never raises**; used by
     `/health` to report degraded rather than crash
   Wire `connect()`/`disconnect()` into `app/main.py`'s `lifespan`, with the
   `connect()` failure logged but non-fatal (see how `app/main.py` handles
   `db.connect()` failing) - Postgres/Redis/Kafka may come up on their own
   schedule and shouldn't block the API from starting.

   AWS (`libs/aws`) is the exception: aioboto3 clients are cheap to open
   per-call, so there's no `connect()`/`disconnect()` there - just methods
   that open a client as an async context manager per call.

5. **Never crash on infra failure inside a `health_check()`.** Wrap the body
   in `try/except Exception: return False`.

6. **Add real dependencies to `pyproject.toml`**, don't rely on transitive
   installs, even if something already pulls the package in indirectly.

7. **Verify it actually works**, not just that it imports:
   - `uv run ruff check .`
   - `uv run python -c "from libs.<name> import ...; print('OK')"`
   - Exercise the real behavior (a throwaway script is fine, delete it after)
     - e.g. confirm a `health_check()` returns `False` against an
       unreachable host rather than raising, or that a retry wrapper
       actually retries and gives up correctly.
   - If the package is wired into `app/main.py`, boot the app
     (`uv run uvicorn app.main:app --port <scratch-port>`) and hit the
     affected routes with `curl`.

## Documentation checklist

Every package needs:

1. A short module docstring at the top of `base.py` explaining what it does
   and why it's decoupled the way it is, plus a minimal usage snippet.
2. A doc page at `docs/libs/<name>.md` with a full setup + usage example
   (see any existing file there for the shape: Setup, Usage, any
   package-specific notes/gotchas).
3. A row added to the table in `docs/libs/README.md`.
4. A row added to the table in the root `README.md`'s "The `libs/` packages"
   section (package name, one-line summary, link to the doc page), and the
   package folder added to the `Project layout` tree near the top of that
   file.
5. If the package's `DatabaseSettings`/`RedisSettings`/`KafkaSettings`/etc.
   (or any config it needs) is meant to be populated from environment
   variables in this project, update `.env.example`:
   - Add the new variables with realistic placeholder values, grouped under
     a comment naming the package (matching the existing "Redis" / "Kafka" /
     "AWS (S3, SQS)" sections).
   - If the package isn't wired into `app/main.py` by default (optional
     infra), add its section commented-out, under the existing
     `# --- Optional infra ---` block, the same way Redis/Kafka/AWS are.
   - If you add a field to `app/core/config.py`'s `Settings` (e.g. a new
     `POSTGRES_*`/`REDIS_*` var), always mirror it into `.env.example` in the
     same change - an env var with no example entry is easy to forget and
     breaks fresh setups silently.

## Updating an existing package

Same rules apply. In particular:
- Don't add an `app`-specific import to "make it easier" - if the package
  needs a new value from settings, add a parameter instead.
- If you change a public function/class signature, update every usage
  example in its `docs/libs/<name>.md` and its module docstring to match -
  stale examples are worse than no examples.
- Re-run the verification steps above before considering the change done.
