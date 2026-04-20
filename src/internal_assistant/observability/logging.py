from __future__ import annotations

import logging
from typing import Any

from pythonjsonlogger.json import JsonFormatter

from internal_assistant.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler()
    formatter = JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_kv(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    logger.info(message, extra={"event": kwargs})
