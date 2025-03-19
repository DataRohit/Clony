"""
Tests for the CLI commit command.

This module contains tests for the commit command in the CLI.
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
from clony.internals.staging import stage_file


# Test fixture for creating a temporary directory
@pytest.fixture
def temp_dir() -> Generator[pathlib.Path, None, None]:
    """
    Create a temporary directory for testing.

    Yields:
        pathlib.Path: Path to the temporary directory.
    """

    # Create a temporary directory
    temp_path = pathlib.Path(tempfile.mkdtemp())

    # Yield the temporary directory path
    yield temp_path

    # Clean up the temporary directory
    shutil.rmtree(temp_path)


# Test for the commit command
@pytest.mark.cli
def test_commit_command(temp_dir: pathlib.Path):
    """
    Test the commit command functionality.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Create a test file in the temp directory
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file.")

    # Stage the test file
    with patch.object(pathlib.Path, "cwd", return_value=temp_dir):
        stage_file(str(test_file_path))

    # Run the commit command
    with patch("clony.cli.make_commit") as mock_commit:
        result = runner.invoke(
            cli,
            [
                "commit",
                "--message",
                "Test commit message",
                "--author-name",
                "Test Author",
                "--author-email",
                "test@example.com",
            ],
        )
        assert result.exit_code == 0
        mock_commit.assert_called_once_with(
            "Test commit message", "Test Author", "test@example.com"
        )


# Test for the commit command with default author values
@pytest.mark.cli
def test_commit_command_default_author(temp_dir: pathlib.Path):
    """
    Test the commit command with default author values.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Create a test file in the temp directory
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file.")

    # Stage the test file
    with patch.object(pathlib.Path, "cwd", return_value=temp_dir):
        stage_file(str(test_file_path))

    # Run the commit command with only the message
    with patch("clony.cli.make_commit") as mock_commit:
        result = runner.invoke(cli, ["commit", "--message", "Test commit message"])
        assert result.exit_code == 0
        mock_commit.assert_called_once_with(
            "Test commit message", "Clony User", "user@example.com"
        )


# Test for the commit command without a message
@pytest.mark.cli
def test_commit_command_no_message(temp_dir: pathlib.Path):
    """
    Test the commit command without a message.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Run the commit command without a message
    result = runner.invoke(cli, ["commit"])
    assert result.exit_code != 0
    assert "Error: Missing option '--message' / '-m'." in result.output


# Test for the commit command with an error
@pytest.mark.cli
def test_commit_command_error(temp_dir: pathlib.Path):
    """
    Test the commit command when an error occurs.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Mock make_commit to raise an exception
    with patch("clony.cli.make_commit", side_effect=Exception("Test error")):
        # Mock the logger.error function to track calls
        with patch("clony.cli.logger.error") as mock_logger:
            # Run the commit command
            result = runner.invoke(cli, ["commit", "--message", "Test commit message"])

            # Verify that the command failed
            assert result.exit_code == 1

            # Verify that logger.error was called with the correct error message
            mock_logger.assert_called_once_with("Error creating commit: Test error")
