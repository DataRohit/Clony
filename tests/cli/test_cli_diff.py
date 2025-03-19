"""
Tests for the diff command in CLI.

This module contains tests for the diff command in the CLI, which is used to
display the differences between two blob objects.
"""

# Standard library imports
import os
import pathlib
import shutil
import tempfile
from typing import Generator
from unittest.mock import patch

# Third-party imports
import pytest
from click.testing import CliRunner

# Local imports
from clony.cli import diff


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

    # Change to the temporary directory
    original_dir = os.getcwd()
    os.chdir(temp_path)

    # Yield the temporary directory path
    yield temp_path

    # Restore the original directory
    os.chdir(original_dir)

    # Clean up the temporary directory
    shutil.rmtree(temp_path)


# Test for the diff command
@pytest.mark.cli
def test_diff_command(temp_dir: pathlib.Path):
    """
    Test the diff command in the CLI.
    """

    # Mock print_diff function
    with patch("clony.cli.print_diff") as mock_print_diff:
        # Run the diff command
        runner = CliRunner()
        result = runner.invoke(diff, ["blob1", "blob2"])

        # Check that the command ran successfully
        assert result.exit_code == 0

        # Check that print_diff was called with the correct arguments
        mock_print_diff.assert_called_once()
        args, kwargs = mock_print_diff.call_args
        assert len(args) >= 2
        assert args[1] == "blob1"
        assert args[2] == "blob2"


# Test for the diff command with options
@pytest.mark.cli
def test_diff_command_with_options(temp_dir: pathlib.Path):
    """
    Test the diff command in the CLI with various options.
    """

    # Mock print_diff function
    with patch("clony.cli.print_diff") as mock_print_diff:
        # Run the diff command with options
        runner = CliRunner()
        result = runner.invoke(
            diff,
            [
                "blob1",
                "blob2",
                "--path1",
                "file1.txt",
                "--path2",
                "file2.txt",
                "--algorithm",
                "unified",
                "--context-lines",
                "5",
            ],
        )

        # Check that the command ran successfully
        assert result.exit_code == 0

        # Check that print_diff was called with the correct arguments
        mock_print_diff.assert_called_once()
        args, kwargs = mock_print_diff.call_args
        assert len(args) >= 2
        assert args[1] == "blob1"
        assert args[2] == "blob2"
        assert args[3] == "file1.txt"
        assert args[4] == "file2.txt"
        assert args[5] == "unified"
        assert args[6] == 5
