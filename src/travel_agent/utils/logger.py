"""Lightweight logging helpers for the Travel Agent service."""

from __future__ import annotations

import logging
from typing import Optional

_LOGGER_CACHE: dict[str, logging.Logger] = {}


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module level logger configured for development."""

    logger_name = name or "travel_agent"
    if logger_name in _LOGGER_CACHE:
        return _LOGGER_CACHE[logger_name]

    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    _LOGGER_CACHE[logger_name] = logger
    return logger
