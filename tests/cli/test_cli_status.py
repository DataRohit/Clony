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


# Test for the status command
@pytest.mark.cli
def test_status_command(temp_dir: pathlib.Path):
    """
    Test that the status command works correctly.
    """

    # Create a test file
    test_file = temp_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write("Test content")

    # Mock the get_status function to return a known status
    status_dict = {status: [] for status in FileStatus}
    status_dict[FileStatus.UNTRACKED] = ["test.txt"]
    formatted_output = (
        "Untracked files:\n"
        '  (use "git add <file>..." to include in what will be committed)\n\n'
        "        test.txt\n"
    )

    with patch("clony.cli.get_status", return_value=(status_dict, formatted_output)):
        # Run the status command
        runner = CliRunner()
        result = runner.invoke(cli, ["status", str(temp_dir)])

        # Check that the command was successful
        assert result.exit_code == 0

        # Check that the output contains the expected status
        assert "On branch main" in result.output
        assert "Untracked files:" in result.output
        assert "test.txt" in result.output


# Test for the status command with the default path
@pytest.mark.cli
def test_status_command_default_path():
    """
    Test that the status command works with the default path.
    """

    # Mock the get_status function to return a known status
    status_dict = {status: [] for status in FileStatus}
    status_dict[FileStatus.UNMODIFIED] = []
    formatted_output = "nothing to commit, working tree clean"

    with patch("clony.cli.get_status", return_value=(status_dict, formatted_output)):
        # Run the status command with no path argument
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])

        # Check that the command was successful
        assert result.exit_code == 0

        # Check that the output contains the expected status
        assert "On branch main" in result.output
        assert "nothing to commit, working tree clean" in result.output


# Test for the status command with an error
@pytest.mark.cli
def test_status_command_error():
    """
    Test that the status command handles errors correctly.
    """

    # Mock the get_status function to raise an exception
    with patch("clony.cli.get_status", side_effect=Exception("Test error")):
        # Run the status command
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])

        # Check that the command failed
        assert result.exit_code == 1

        # Check that the output contains the error message
        assert "Error:" in result.output
        assert "Test error" in result.output
