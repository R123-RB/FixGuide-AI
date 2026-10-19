"""Structured logging setup."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from loguru import logger

from fixguide.config import get_settings


def setup_logging() -> Any:  # noqa: ANN401
    """Configure structured logging."""
    settings = get_settings()

    logger.remove()

    # Console output
    logger.add(
        sys.stdout,
        level=settings.logging.level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File output (JSON)
    log_file = Path(settings.logging.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_file,
        level=settings.logging.level,
        format="{time} {level} {name} {function} {line} {message}",
        serialize=settings.logging.format == "json",
        rotation="10 MB",
        retention="7 days",
    )

    return logger
