"""Single source of truth for the starlette Config loader.

All settings classes import `config` from here — never instantiate
Config themselves. This ensures a single .env file resolution across
the entire application.
"""

import logging
import os

from starlette.config import Config

logger = logging.getLogger(__name__)

current_file_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, "..", "..", "..", ".."))

env_paths = [
    "/app/.env",
    os.path.join(project_root, ".env"),
    "/.env",
]

env_path = next((path for path in env_paths if os.path.isfile(path)), env_paths[0])
logger.info(f"Using environment file at: {env_path}")

config = Config(env_path)