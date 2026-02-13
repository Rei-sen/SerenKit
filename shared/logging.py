"""Logging utilities for consistent, structured logging throughout addon."""

import logging

from typing import Optional

# Module-level logger
_logger: Optional[logging.Logger] = None


def init_logger(addon_name: str = "Modkit") -> logging.Logger:
    """Initialize and return the addon logger."""
    global _logger

    if _logger is not None:
        return _logger

    _logger = logging.getLogger(addon_name)
    _logger.setLevel(logging.DEBUG)

    # Console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    # Formatter with addon prefix
    formatter = logging.Formatter(f'[{addon_name}] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)

    if not _logger.handlers:
        _logger.addHandler(handler)

    return _logger


def get_logger() -> logging.Logger:
    """Return the addon logger, initializing if necessary."""
    global _logger
    if _logger is None:
        _logger = init_logger()
    return _logger


def log_debug(message: str) -> None:
    """Log debug message."""
    get_logger().debug(message)


def log_info(message: str) -> None:
    """Log info message."""
    get_logger().info(message)


def log_warning(message: str) -> None:
    """Log warning message."""
    get_logger().warning(message)


def log_error(message: str) -> None:
    """Log error message."""
    get_logger().error(message)


def log_exception(message: str = "Exception occurred") -> None:
    """Log exception with traceback."""
    get_logger().exception(message)
