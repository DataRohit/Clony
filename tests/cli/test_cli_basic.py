"""
Tests for basic CLI functionality.

This module contains tests for basic Clony CLI functionality like help, version,
and no args.
"""

# Standard imports
from unittest.mock import patch

# Third-party imports
import pytest
from click.testing import CliRunner

# Local imports
from clony import __version__
from clony.cli import cli


# Test for the CLI help command with --help
@pytest.mark.cli
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
@pytest.mark.cli
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
@pytest.mark.cli
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
@pytest.mark.cli
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


# Test for the help command
@pytest.mark.cli
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
        mock_help.assert_called_once_with(mock_help.call_args[0][0], show_logo=False)
