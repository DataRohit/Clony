"""
Tests for the CLI module.

This module contains tests for the Clony CLI functionality.
"""

# Standard imports
from unittest.mock import MagicMock, patch

from click import Option

# Third-party imports
from click.testing import CliRunner

# Local imports
from clony import __version__
from clony.cli import cli, display_logo, display_stylized_help, main


# Test for the CLI help command with --help
def test_cli_help():
    """
    Test that the CLI help command works correctly with --help.
    """

    # Mock the display_stylized_help function
    with patch("clony.cli.display_stylized_help") as mock_help:
        # Run the CLI with --help
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        # Assert that the exit code is 0
        assert result.exit_code == 0

        # Assert that the display_stylized_help function was called once
        mock_help.assert_called_once()


# Test for the CLI help command with -h
def test_cli_help_shorthand():
    """
    Test that the CLI help command works correctly with -h shorthand.
    """

    # Mock the display_stylized_help function
    with patch("clony.cli.display_stylized_help") as mock_help:
        # Run the CLI with -h
        runner = CliRunner()
        result = runner.invoke(cli, ["-h"])

        # Assert that the exit code is 0
        assert result.exit_code == 0

        # Assert that the display_stylized_help function was called once
        mock_help.assert_called_once()


# Test for the CLI version command
def test_cli_version():
    """
    Test that the CLI version command works correctly.
    """

    # Mock the display_logo function
    with patch("clony.cli.display_logo"):
        # Run the CLI with --version
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        # Assert that the exit code is 0
        assert result.exit_code == 0

        # Assert that the version is in the output
        assert __version__ in result.output


# Test for the CLI with no arguments
def test_cli_no_args():
    """
    Test that the CLI works correctly when no arguments are provided.
    """

    # Mock the display_stylized_help function
    with patch("clony.cli.display_stylized_help") as mock_help:
        # Run the CLI with no arguments
        with patch("clony.cli.display_logo"):
            # Run the CLI with no arguments
            runner = CliRunner()
            result = runner.invoke(cli)

            # Assert that the exit code is 0
            assert result.exit_code == 0

            # Assert that the display_stylized_help function was called once
            mock_help.assert_called_once_with(
                mock_help.call_args[0][0], show_logo=False
            )


# Test for the display_logo function
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


# Test for the help command
def test_help_command():
    """
    Test that the help command works correctly.
    """

    # Mock the display_stylized_help function
    with patch("clony.cli.display_stylized_help") as mock_help:
        # Run the help command
        runner = CliRunner()
        result = runner.invoke(cli, ["help"])

        # Assert that the exit code is 0
        assert result.exit_code == 0

        # Assert that the display_stylized_help function was called once
        mock_help.assert_called_once_with(mock_help.call_args[0][0], show_logo=False)


# Test for the main function with successful execution
def test_main_success():
    """
    Test that the main function works correctly with successful execution.
    """

    # Mock the cli function
    with patch("clony.cli.cli") as mock_cli:
        # Mock the sys.exit function
        with patch("sys.exit") as mock_exit:
            # Run the main function
            main()

            # Assert that the cli function was called once
            mock_cli.assert_called_once()

            # Assert that the sys.exit function was not called
            mock_exit.assert_not_called()


# Test for the main function with an exception
def test_main_exception():
    """
    Test that the main function handles exceptions correctly.
    """

    # Mock the cli function
    with patch("clony.cli.cli", side_effect=Exception("Test error")):
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Mock the sys.exit function
            with patch("sys.exit") as mock_exit:
                # Run the main function
                main()

                # Assert that the console.print function was called once
                mock_print.assert_called_once()

                # Assert that the sys.exit function was called once with 1
                mock_exit.assert_called_once_with(1)
