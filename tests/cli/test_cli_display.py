"""
Tests for CLI display functionality.

This module contains tests for Clony CLI display functionality like logo
and stylized help.
"""

# Standard imports
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest
from click import Option

# Local imports
from clony.cli import display_logo, display_stylized_help


# Test for the display_logo function
@pytest.mark.unit
def test_display_logo():
    """
    Test that the display_logo function works correctly.
    """

    # Mock the console.print function
    with patch("clony.cli.console.print") as mock_print:
        # Run the display_logo function
        display_logo()

        # Assert that the console.print function was called once
        mock_print.assert_called_once()


# Test for the display_stylized_help function with no commands
@pytest.mark.unit
def test_display_stylized_help_no_commands():
    """
    Test that the display_stylized_help function works correctly with no commands.
    """

    # Create a mock context
    mock_ctx = MagicMock()
    mock_ctx.command.help = "Test help text"
    mock_ctx.command.params = []
    mock_ctx.command.commands = {}

    # Mock the display_logo function
    with patch("clony.cli.display_logo") as mock_logo:
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Run the display_stylized_help function
            display_stylized_help(mock_ctx)

            # Assert that the display_logo function was called once
            mock_logo.assert_called_once()

            # Assert that the console.print function was called at least twice
            assert mock_print.call_count >= 2


# Test for the display_stylized_help function with show_logo=False
@pytest.mark.unit
def test_display_stylized_help_no_logo():
    """
    Test that the display_stylized_help function works correctly with show_logo=False.
    """

    # Create a mock context
    mock_ctx = MagicMock()
    mock_ctx.command.help = "Test help text"
    mock_ctx.command.params = []
    mock_ctx.command.commands = {}

    # Mock the display_logo function
    with patch("clony.cli.display_logo") as mock_logo:
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Run the display_stylized_help function
            display_stylized_help(mock_ctx, show_logo=False)

            # Assert that the display_logo function was not called
            mock_logo.assert_not_called()

            # Assert that the console.print function was called at least twice
            assert mock_print.call_count >= 2


# Test for the display_stylized_help function with commands
@pytest.mark.unit
def test_display_stylized_help_with_commands():
    """
    Test that the display_stylized_help function works correctly with commands.
    """

    # Create a mock command
    mock_cmd = MagicMock()
    mock_cmd.help = "Test command help"

    # Create a mock context
    mock_ctx = MagicMock()
    mock_ctx.command.help = "Test help text"
    mock_ctx.command.params = []
    mock_ctx.command.commands = {"test-cmd": mock_cmd}

    # Mock the display_logo function
    with patch("clony.cli.display_logo") as mock_logo:
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Run the display_stylized_help function
            display_stylized_help(mock_ctx)

            # Assert that the display_logo function was called once
            mock_logo.assert_called_once()

            # Assert that the console.print function was called at least three times
            assert mock_print.call_count >= 3


# Test for the display_stylized_help function with options
@pytest.mark.unit
def test_display_stylized_help_with_options():
    """
    Test that the display_stylized_help function works correctly with options.
    """

    # Create a mock option
    mock_option = MagicMock(spec=Option)
    mock_option.opts = ["--test"]
    mock_option.secondary_opts = ["-t"]
    mock_option.help = "Test option help"

    # Create a mock context
    mock_ctx = MagicMock()
    mock_ctx.command.help = "Test help text"
    mock_ctx.command.params = [mock_option]
    mock_ctx.command.commands = {}

    # Mock the display_logo function
    with patch("clony.cli.display_logo") as mock_logo:
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Run the display_stylized_help function
            display_stylized_help(mock_ctx)

            # Assert that the display_logo function was called once
            mock_logo.assert_called_once()

            # Assert that the console.print function was called at least three times
            assert mock_print.call_count >= 3


# Test for the display_stylized_help function with commands and options
@pytest.mark.unit
def test_display_stylized_help_with_commands_and_options():
    """
    Test that the display_stylized_help function works correctly with both
    commands and options.
    """

    # Create a mock command
    mock_cmd = MagicMock()
    mock_cmd.help = "Test command help"

    # Create a mock option
    mock_option = MagicMock(spec=Option)
    mock_option.opts = ["--test"]
    mock_option.secondary_opts = ["-t"]
    mock_option.help = "Test option help"

    # Create a mock context
    mock_ctx = MagicMock()
    mock_ctx.command.help = "Test help text"
    mock_ctx.command.params = [mock_option]
    mock_ctx.command.commands = {"test-cmd": mock_cmd}

    # Mock the display_logo function
    with patch("clony.cli.display_logo") as mock_logo:
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Run the display_stylized_help function
            display_stylized_help(mock_ctx)

            # Assert that the display_logo function was called once
            mock_logo.assert_called_once()

            # Assert that the console.print function was called at least four times
            assert mock_print.call_count >= 4
            assert mock_print.call_count >= 4
