"""
Tests for the CLI status command.

This module contains tests for the status command in the CLI.
"""

# Standard library imports
import pathlib
import shutil
import tempfile
from typing import Generator
from unittest.mock import patch

# Third-party imports
import pytest
from click.testing import CliRunner

# Local imports
from clony.cli import cli
from clony.internals.status import FileStatus


# Test fixture for creating a temporary directory
@pytest.fixture
def temp_dir() -> Generator[pathlib.Path, None, None]:
    """
    Create a temporary directory for testing.

    Yields:
        pathlib.Path: Path to the temporary directory.
    """

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Convert to Path object
        temp_path = pathlib.Path(temp_dir)

        # Initialize a git repository
        with patch("clony.core.repository.logger"):
            runner = CliRunner()
            runner.invoke(cli, ["init", str(temp_path)])

        # Yield the temporary directory
        yield temp_path

        # Clean up
        shutil.rmtree(temp_path, ignore_errors=True)


# Test for the status command with tabular output
@pytest.mark.cli
def test_status_command_tabular_output(temp_dir: pathlib.Path):
    """
    Test that the status command with tabular output works correctly.

    This test verifies that the status command correctly displays repository
    status in tabular format using the display_status_info function.

    Args:
        temp_dir: Path to the temporary directory.
    """
    # Create a test file
    test_file = temp_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write("Test content")

    # Create a mock status dictionary
    status_dict = {status: [] for status in FileStatus}
    status_dict[FileStatus.UNTRACKED] = ["test.txt"]

    # Mock the get_status function and display_status_info
    with (
        patch(
            "clony.cli.get_status", return_value=(status_dict, "")
        ) as mock_get_status,
        patch("clony.internals.status.display_status_info") as mock_display,
    ):
        # Run the status command
        runner = CliRunner()
        result = runner.invoke(cli, ["status", str(temp_dir)])

        # Check that the command was successful
        assert result.exit_code == 0

        # Verify that get_status was called with the correct path
        mock_get_status.assert_called_once_with(str(temp_dir))

        # Verify that display_status_info was called with the status dictionary
        mock_display.assert_called_once_with(status_dict)


# Test for the status command with the default path
@pytest.mark.cli
def test_status_command_default_path():
    """
    Test that the status command works with the default path.

    This test verifies that the status command correctly uses the default path
    and displays the status in tabular format.
    """
    # Create a mock status dictionary
    status_dict = {status: [] for status in FileStatus}

    # Mock the get_status function and display_status_info
    with (
        patch(
            "clony.cli.get_status", return_value=(status_dict, "")
        ) as mock_get_status,
        patch("clony.internals.status.display_status_info") as mock_display,
    ):
        # Run the status command with no path argument
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])

        # Check that the command was successful
        assert result.exit_code == 0

        # Verify that get_status was called with the default path
        mock_get_status.assert_called_once_with(".")

        # Verify that display_status_info was called with the status dictionary
        mock_display.assert_called_once_with(status_dict)


# Test for the status command with an error
@pytest.mark.cli
def test_status_command_error():
    """
    Test that the status command handles errors correctly.

    This test verifies that the status command properly handles and reports
    errors that occur during execution.
    """
    # Mock the get_status function to raise an exception
    with patch("clony.cli.get_status", side_effect=Exception("Test error")):
        # Mock the logger.error function to track calls
        with patch("clony.cli.logger.error") as mock_logger:
            # Run the status command
            runner = CliRunner()
            result = runner.invoke(cli, ["status"])

            # Check that the command failed
            assert result.exit_code == 1

            # Check that logger.error was called with the correct error message
            mock_logger.assert_called_once_with("Error showing status: Test error")


@pytest.mark.cli
def test_status_command():
    """
    Test the status command.

    This test verifies that the status command correctly calls the get_status
    and display_status_info functions, and displays the appropriate branch information.
    """
    # Create a mock status dictionary
    status_dict = {status: [] for status in FileStatus}

    with (
        patch(
            "clony.cli.get_status", return_value=(status_dict, "")
        ) as mock_get_status,
        patch("clony.internals.status.display_status_info") as mock_display,
        patch("clony.cli.logger.info") as mock_logger_info,
    ):
        # Call the status command
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])

        # Verify the result
        assert result.exit_code == 0

        # Verify that get_status was called with the correct path
        mock_get_status.assert_called_once_with(".")

        # Verify that display_status_info was called with the status dictionary
        mock_display.assert_called_once_with(status_dict)

        # Verify that branch information was logged
        mock_logger_info.assert_any_call("On branch main")
