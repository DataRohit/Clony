"""
Logging configuration for Clony.

This module provides rich colorful logging functionality using the Rich library.
"""

# Standard library imports
import logging
import sys
from typing import Optional, Union

# Third-party imports
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme


# Helper function to remove handlers - this allows for better testing
def _remove_handlers(logger_instance: logging.Logger) -> None:
    """
    Remove all handlers from a logger instance.

    Args:
        logger_instance: The logger instance to remove handlers from.
    """
    for handler in logger_instance.handlers[:]:
        logger_instance.removeHandler(handler)


# Define custom theme with colors for different log levels
custom_theme = Theme(
    {
        "info": "green",
        "warning": "yellow",
        "error": "red",
        "debug": "dim blue",
    }
)

# Initialize Rich console with custom theme
console = Console(theme=custom_theme)

# Create a custom logger
logger = logging.getLogger("clony")
logger.setLevel(logging.INFO)

# Remove any existing handlers to avoid duplicates
_remove_handlers(logger)

# Create Rich handler for colorful output
rich_handler = RichHandler(
    console=console,
    show_path=False,
    omit_repeated_times=True,
    rich_tracebacks=True,
    tracebacks_show_locals=True,
)
# Set handler level to match logger level
rich_handler.setLevel(logger.level)

# Set the formatter for the handler
formatter = logging.Formatter("%(message)s")
rich_handler.setFormatter(formatter)

# Add handler to the logger
logger.addHandler(rich_handler)

# Set propagate to True in test environments to allow caplog to capture messages
# This enables capturing log output during tests
if "pytest" in sys.modules:
    logger.propagate = True
else:
    logger.propagate = False


# Setup logger
def setup_logger(
    name: str = "clony", level: Optional[Union[str, int]] = None
) -> logging.Logger:
    """
    Set up a Rich-powered colorful logger instance.

    This function creates or retrieves a logger with Rich formatting for
    beautiful, readable console output with proper color coding by log level.

    Args:
        name: The name of the logger. Defaults to "clony".
        level: The logging level as string or int. Defaults to INFO if None.

    Returns:
        logging.Logger: A configured logger instance with Rich formatting.
    """

    # Return the existing logger if it's already set up
    if name == "clony":
        return logger

    # Create a new logger instance
    new_logger = logging.getLogger(name)

    # Remove any existing handlers to avoid duplicates
    _remove_handlers(new_logger)

    # Set the logging level - handle both string and integer level values
    if level is None:
        log_level = logging.INFO
    elif isinstance(level, str):
        log_level = getattr(logging, level.upper())
    else:
        # If it's already an integer level value, use it directly
        log_level = level

    new_logger.setLevel(log_level)

    # Create a new Rich handler for this logger with matching level
    new_handler = RichHandler(
        console=console,
        show_path=False,
        omit_repeated_times=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )
    new_handler.setLevel(log_level)
    new_handler.setFormatter(formatter)
    new_logger.addHandler(new_handler)

    # Set propagate based on environment
    if "pytest" in sys.modules:
        new_logger.propagate = True
    else:
        new_logger.propagate = False

    # Return the new logger
    return new_logger
