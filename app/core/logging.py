"""
Basic application logging setup.

Kept intentionally simple for Phase 1 — structured/observability logging
can be layered on in a later phase if needed.
"""
import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure root logging handlers/format. Safe to call multiple times."""
    settings = get_settings()

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    # Avoid duplicate handlers if configure_logging() is called more than once
    # (e.g. during tests importing the app multiple times).
    if root_logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Convenience accessor for module-level loggers."""
    return logging.getLogger(name)
