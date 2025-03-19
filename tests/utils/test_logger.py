"""
Tests for the logging functionality.

This module contains tests for the logger configuration and usage.
"""

# Standard library imports
import importlib
import logging
import sys

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


# Test logger propagation in test environment
@pytest.mark.unit
def test_logger_propagation_test():
    """
    Test that logger propagation is enabled in test environments.
    """

    # Create a test logger
    logger = setup_logger("test_logger")

    # Check that propagation is enabled in test environments
    assert "pytest" in sys.modules
    assert logger.propagate


# Test logger propagation in non-test environment
@pytest.mark.unit
def test_logger_propagation_non_test():
    """
    Test that logger propagation is disabled in non-test environments.
    """

    # Save the original sys.modules and logger state
    original_modules = dict(sys.modules)
    original_logger = logging.getLogger("clony")
    original_propagate = original_logger.propagate
    original_handlers = list(original_logger.handlers)

    try:
        # Remove pytest from sys.modules to simulate non-test environment
        if "pytest" in sys.modules:
            del sys.modules["pytest"]

        # Reset the logger configuration
        original_logger.propagate = False
        original_logger.handlers.clear()

        # Create a test logger
        logger = setup_logger("test_logger")

        # Check that propagation is disabled
        assert not logger.propagate

        # Create another logger to test the main logger configuration
        main_logger = setup_logger()
        assert not main_logger.propagate

    finally:
        # Restore the original sys.modules and logger state
        sys.modules.clear()
        sys.modules.update(original_modules)
        original_logger.propagate = original_propagate
        original_logger.handlers.clear()
        original_logger.handlers.extend(original_handlers)


# Test logger module initialization in non-test environment
@pytest.mark.unit
def test_logger_module_init_non_test():
    """
    Test that the logger module initializes correctly in a non-test environment.
    """

    # Save the original sys.modules and logger state
    original_modules = dict(sys.modules)
    original_logger = logging.getLogger("clony")
    original_propagate = original_logger.propagate
    original_handlers = list(original_logger.handlers)

    try:
        # Remove pytest from sys.modules to simulate non-test environment
        if "pytest" in sys.modules:
            del sys.modules["pytest"]

        # Remove the logger module from sys.modules to force reinitialization
        if "clony.utils.logger" in sys.modules:
            del sys.modules["clony.utils.logger"]

        # Reset the logger configuration
        original_logger.propagate = False
        original_logger.handlers.clear()

        # Import the logger module in a non-test environment
        importlib.import_module("clony.utils.logger")

        # Get the logger and check its configuration
        logger = logging.getLogger("clony")
        assert not logger.propagate

    finally:
        # Restore the original sys.modules and logger state
        sys.modules.clear()
        sys.modules.update(original_modules)
        original_logger.propagate = original_propagate
        original_logger.handlers.clear()
        original_logger.handlers.extend(original_handlers)


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


# Test setup_logger with existing logger
@pytest.mark.unit
def test_setup_logger_existing():
    """
    Test that setup_logger returns the existing logger for 'clony'.
    """

    # Get the main logger
    main_logger = setup_logger()

    # Get another instance
    another_logger = setup_logger()

    # Check that they are the same object
    assert main_logger is another_logger
    assert main_logger.name == "clony"
