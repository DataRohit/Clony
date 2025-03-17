"""
Logging configuration for Clony.

This module provides colorful logging functionality using colorlog.
"""

# Standard library imports
import logging
import sys
from typing import Optional

# Third party imports
import colorlog


# Setup a colorful logger instance
def setup_logger(name: str = "clony", level: Optional[str] = None) -> logging.Logger:
    """
    Set up a colorful logger instance.

    Args:
        name: The name of the logger. Defaults to "clony".
        level: The logging level. Defaults to INFO if None.

    Returns:
        logging.Logger: A configured logger instance.
    """

    # Create a logger instance
    logger = colorlog.getLogger(name)

    # Set the logging level
    log_level = getattr(logging, level.upper()) if level else logging.INFO
    logger.setLevel(log_level)

    # Create a color formatter
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(message_log_color)s%(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={
            "message": {
                "DEBUG": "cyan",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            }
        },
        style="%",
    )

    # Create and configure a console handler
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Remove any existing handlers and add the new one
    logger.handlers.clear()
    logger.addHandler(console_handler)

    # Prevent the logger from propagating to the root logger
    logger.propagate = False

    # Return the logger instance
    return logger


# Create a default logger instance
logger = setup_logger()
