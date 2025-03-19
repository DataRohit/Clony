"""
Logging configuration for Clony.

This module provides colorful logging functionality using colorlog.
"""

# Standard library imports
import logging
import sys
from typing import Optional

from colorama import Fore, Style, init

# Initialize colorama
init(strip=False, convert=True, autoreset=False)

# Create a custom logger
logger = logging.getLogger("clony")
logger.setLevel(logging.INFO)

# Create handlers - only use one handler to avoid duplicates
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)


# Create formatters and add it to handlers
class ColorFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.INFO:
            prefix = f"{Fore.GREEN}INFO{Style.RESET_ALL}"
        elif record.levelno == logging.WARNING:
            prefix = f"{Fore.YELLOW}WARNING{Style.RESET_ALL}"
        elif record.levelno == logging.ERROR:
            prefix = f"{Fore.RED}ERROR{Style.RESET_ALL}"
        else:
            prefix = f"{Style.RESET_ALL}DEBUG{Style.RESET_ALL}"

        # Format the message with the appropriate prefix
        record.msg = f"{prefix} {record.msg}"
        return super().format(record)


formatter = ColorFormatter("%(message)s")
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)

# Set propagate to False to prevent duplicate logs
logger.propagate = False


def setup_logger(name: str = "clony", level: Optional[str] = None) -> logging.Logger:
    """
    Set up a colorful logger instance.

    Args:
        name: The name of the logger. Defaults to "clony".
        level: The logging level. Defaults to INFO if None.

    Returns:
        logging.Logger: A configured logger instance.
    """
    # Return the existing logger if it's already set up
    if name == "clony":
        return logger

    # Create a new logger instance
    new_logger = logging.getLogger(name)

    # Set the logging level
    log_level = getattr(logging, level.upper()) if level else logging.INFO
    new_logger.setLevel(log_level)

    # Add the same handlers as the main logger
    new_logger.addHandler(console_handler)

    # Prevent the logger from propagating to the root logger
    new_logger.propagate = False

    return new_logger
