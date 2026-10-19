# backend/app/core/logging_config.py
"""
Structured logging setup for the application. Called once at startup
by main.py before the FastAPI app is created, so every module's
`logging.getLogger(...)` calls (across services/, ai/agents/,
integrations/, etc.) inherit consistent formatting.
"""

import logging
import sys

from app.core.config import get_settings

settings = get_settings()

LOG_FORMAT_DEV = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_FORMAT_PROD = (
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
    '"logger": "%(name)s", "message": "%(message)s"}'
)

# Third-party loggers that are noisy at INFO level and drown out our
# own application logs — silenced to WARNING regardless of environment.
NOISY_LOGGERS = [
    "uvicorn.access",
    "motor",
    "pymongo",
    "httpx",
    "httpcore",
    "google.auth",
    "chromadb",
]


def configure_logging() -> None:
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO
    log_format = LOG_FORMAT_PROD if settings.is_production else LOG_FORMAT_DEV

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any pre-existing handlers (e.g. uvicorn's default) to avoid
    # duplicate log lines when this is called during app startup.
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))
    root_logger.addHandler(handler)

    for logger_name in NOISY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    logging.getLogger("ai_email_os").setLevel(log_level)