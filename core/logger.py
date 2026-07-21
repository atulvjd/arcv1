"""
ArcV1 Logging Framework

Centralized logging for the entire ArcV1 runtime.
"""

from __future__ import annotations

import logging
from pathlib import Path

# ---------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "arcv1.log"

# ---------------------------------------------------------------------
# Colored Formatter
# ---------------------------------------------------------------------


class ColoredFormatter(logging.Formatter):
    """ANSI colored log formatter."""

    COLORS = {
        "DEBUG": "\033[90m",      # Grey
        "INFO": "\033[94m",       # Blue
        "WARNING": "\033[93m",    # Yellow
        "ERROR": "\033[91m",      # Red
        "CRITICAL": "\033[95m",   # Magenta
    }

    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


# ---------------------------------------------------------------------
# Logger Factory
# ---------------------------------------------------------------------


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.

    Parameters
    ----------
    name : str
        Name of the logger.

    Returns
    -------
    logging.Logger
    """

    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = ColoredFormatter(
        "[%(asctime)s] %(levelname)-8s %(name)s : %(message)s",
        "%H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s : %(message)s",
            "%H:%M:%S",
        )
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger