"""
Tests for the Rich logging functionality.

This module contains tests for the Rich logger configuration and usage.
"""

# Standard library imports
import importlib
import logging
import sys

# Third party imports
import pytest
from rich.logging import RichHandler

# Local imports
from clony.utils.logger import _remove_handlers, setup_logger


# Test logger creation
@pytest.mark.unit
def test_logger_creation():
    """
    Test that a logger is created with the correct name and level.

    This test verifies that the setup_logger function creates a logger
    with the specified name and the default INFO level.
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

    This test verifies that the setup_logger function correctly sets
    the specified logging level for the logger.
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
    Test that the logger is configured with the correct Rich handler.

    This test verifies that the logger has exactly one handler and that
    the handler is a RichHandler instance for colorful output.
    """

    # Create a test logger
    logger = setup_logger("test_logger")

    # Check that exactly one handler is configured
    assert len(logger.handlers) == 1

    # Verify handler type is RichHandler
    assert isinstance(logger.handlers[0], RichHandler)


# Test logger propagation in test environment
@pytest.mark.unit
def test_logger_propagation_test():
    """
    Test that logger propagation is enabled in test environments.

    This test verifies that when running in a test environment (with pytest),
    the logger's propagate property is set to True.
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

    This test simulates a non-test environment by removing pytest from
    sys.modules and verifies that logger propagation is disabled.
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

    This test simulates a non-test environment and verifies that
    the logger initializes with the correct propagation settings.
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


# Test rich handler settings
@pytest.mark.unit
def test_rich_handler_settings():
    """
    Test that the RichHandler is configured with the correct settings.

    This test verifies that the RichHandler used by the logger is
    configured with the appropriate settings for rich formatting.
    """

    # Create a test logger
    logger = setup_logger("test_handler_logger")

    # Verify handler is RichHandler
    handler = logger.handlers[0]
    assert isinstance(handler, RichHandler)

    # Check handler settings - check for the presence of attributes
    # but don't test specific values as they might change with Rich versions
    assert hasattr(handler, "console")
    assert hasattr(handler, "rich_tracebacks")
    assert hasattr(handler, "tracebacks_show_locals")


# Test setup_logger with existing logger
@pytest.mark.unit
def test_setup_logger_existing():
    """
    Test that setup_logger returns the existing logger for 'clony'.

    This test verifies that multiple calls to setup_logger with the
    default name return the same logger instance.
    """

    # Get the main logger
    main_logger = setup_logger()

    # Get another instance
    another_logger = setup_logger()

    # Check that they are the same object
    assert main_logger is another_logger
    assert main_logger.name == "clony"


# Test logger with integer level
@pytest.mark.unit
def test_logger_integer_level():
    """
    Test that a logger can be created with an integer level value.

    This test verifies that the setup_logger function correctly handles
    integer logging level values.
    """

    # Create a logger with an integer level
    debug_logger = setup_logger("int_level_logger", logging.DEBUG)

    # Check level is set correctly
    assert debug_logger.level == logging.DEBUG


# Test handler setup with non-string levels
@pytest.mark.unit
def test_setup_with_level_integer():
    """
    Test that setup_logger correctly handles integer level values.

    This test ensures the setup_logger function properly processes
    both string and integer level values.
    """

    # Create a logger with both types of level arguments
    str_logger = setup_logger("str_level_logger", "ERROR")
    int_logger = setup_logger("int_level_logger", logging.WARNING)

    # Check both loggers have correct levels
    assert str_logger.level == logging.ERROR
    assert int_logger.level == logging.WARNING


# Test handler removal
@pytest.mark.unit
def test_logger_handler_removal():
    """
    Test that existing handlers are removed when setting up a logger.

    This test verifies that the setup_logger function correctly removes
    any existing handlers before adding the Rich handler.
    """

    # Create a temporary logger
    temp_logger_name = "temp_handler_removal_logger"
    temp_logger = logging.getLogger(temp_logger_name)

    # Add a temporary handler
    temp_handler = logging.StreamHandler()
    temp_logger.addHandler(temp_handler)

    # Verify handler is present
    assert len(temp_logger.handlers) == 1

    # Call setup_logger which should remove existing handlers
    new_logger = setup_logger(temp_logger_name)

    # We should still have just one handler (the Rich handler)
    assert len(new_logger.handlers) == 1
    assert isinstance(new_logger.handlers[0], RichHandler)

    # Clean up
    for handler in temp_logger.handlers[:]:
        temp_logger.removeHandler(handler)


# Test the _remove_handlers helper function
@pytest.mark.unit
def test_remove_handlers():
    """
    Test the _remove_handlers function directly.

    This test verifies that the _remove_handlers function correctly
    removes all handlers from a logger instance.
    """
    # Create a test logger
    test_logger = logging.getLogger("test_remove_handlers_logger")

    # Add multiple handlers
    handler1 = logging.StreamHandler()
    handler2 = logging.StreamHandler()
    test_logger.addHandler(handler1)
    test_logger.addHandler(handler2)

    # Verify handlers are present
    assert len(test_logger.handlers) == 2

    # Call the remove handlers function
    _remove_handlers(test_logger)

    # Verify all handlers were removed
    assert len(test_logger.handlers) == 0
