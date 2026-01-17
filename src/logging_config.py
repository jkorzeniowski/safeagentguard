"""Centralized logging configuration for SafeAgentGuard."""

import logging
import sys

# Format with fixed-width fields for readable logs
# name: 10 chars, levelname: 8 chars (to fit CRITICAL)
LOG_FORMAT = "%(asctime)s - %(name)-10.10s - %(levelname)-5.5s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure logging for the application.

    Args:
        level: Logging level (default: INFO).
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stderr,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
