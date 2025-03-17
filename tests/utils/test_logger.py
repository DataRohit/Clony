"""
Tests for the logging functionality.

This module contains tests for the logger configuration and usage.
"""

# Standard library imports
import logging

# Third party imports
import pytest

# Local imports
from clony.utils.logger import setup_logger


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
    Test that the logger is configured with the correct handler.
    """

    # Create a test logger
    logger = setup_logger("test_logger")

    # Check that exactly one handler is configured
    assert len(logger.handlers) == 1

    # Check that the handler is a StreamHandler
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)

    # Check that the handler has a formatter
    assert handler.formatter is not None


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
