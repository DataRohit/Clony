"""
Tests for the logging functionality.

This module contains tests for the logger configuration and usage.
"""

# Standard library imports
import logging

# Third party imports
import pytest

# Local imports
from clony.utils.logger import ColorFormatter, setup_logger


# Test logger creation
@pytest.mark.unit
def test_logger_creation():
    """
    Test that a logger is created with the correct name and level.
    """

    # Create a test logger
    logger = setup_logger("test_logger")

    # Check logger name
    assert logger.name == "test_logger"

    # Check default level is INFO
    assert logger.level == logging.INFO


# Test logger custom level
@pytest.mark.unit
def test_logger_custom_level():
    """
    Test that a logger can be created with a custom level.
    """

    # Create loggers with different levels
    debug_logger = setup_logger("debug_logger", "DEBUG")
    warn_logger = setup_logger("warn_logger", "WARNING")

    # Check levels are set correctly
    assert debug_logger.level == logging.DEBUG
    assert warn_logger.level == logging.WARNING


# Test logger handler configuration
@pytest.mark.unit
def test_logger_handler_configuration():
    """
    Test that the logger is configured with the correct handlers.
    """

    # Create a test logger
    logger = setup_logger("test_logger")

    # Check that exactly one handler is configured (StreamHandler)
    assert len(logger.handlers) == 1

    # Verify handler type
    assert isinstance(logger.handlers[0], logging.StreamHandler)


# Test logger propagation
@pytest.mark.unit
def test_logger_propagation():
    """
    Test that logger propagation is disabled.
    """

    # Create a test logger
    logger = setup_logger("test_logger")

    # Check that propagation is disabled
    assert not logger.propagate


# Test color formatter debug level
@pytest.mark.unit
def test_color_formatter_debug():
    """
    Test that the ColorFormatter handles debug level correctly.
    """

    # Create a formatter
    formatter = ColorFormatter("%(message)s")

    # Create a record
    record = logging.LogRecord(
        "test", logging.DEBUG, "test.py", 1, "test message", None, None
    )

    # Format the record
    formatted = formatter.format(record)

    # Check that the formatted message contains the debug prefix
    assert "DEBUG" in formatted


# Test setup logger existing
@pytest.mark.unit
def test_setup_logger_existing():
    """
    Test that setup_logger returns existing logger for 'clony'.
    """

    # Create two loggers
    logger1 = setup_logger("clony")
    logger2 = setup_logger("clony")

    # Check that the two loggers are the same
    assert logger1 is logger2
