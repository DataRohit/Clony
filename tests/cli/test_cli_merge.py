"""
Tests for the CLI merge command.

This module contains tests for the merge command in the CLI.
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


# Test for the merge command with successful merge
@pytest.mark.cli
def test_merge_command_success(temp_dir: pathlib.Path):
    """
    Test the merge command functionality with successful merge.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Mock the validate_commit_reference function to return True
    with patch("clony.cli.validate_commit_reference", return_value=True):
        # Mock the perform_merge function to return 0 conflicts
        with patch("clony.cli.perform_merge", return_value=0) as mock_merge:
            # Run the merge command
            result = runner.invoke(cli, ["merge", "base_commit", "other_commit"])

            # Assert that the command was successful
            assert result.exit_code == 0

            # Assert that perform_merge was called with correct args
            mock_merge.assert_called_once_with("base_commit", "other_commit")


# Test for the merge command with conflicts
@pytest.mark.cli
def test_merge_command_conflicts(temp_dir: pathlib.Path):
    """
    Test the merge command functionality with conflicts.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Mock the validate_commit_reference function to return True
    with patch("clony.cli.validate_commit_reference", return_value=True):
        # Mock the perform_merge function to return conflicts
        with patch("clony.cli.perform_merge", return_value=2) as mock_merge:
            # Run the merge command
            result = runner.invoke(cli, ["merge", "base_commit", "other_commit"])

            # Assert that the command exits with code 1 due to conflicts
            assert result.exit_code == 1

            # Assert that perform_merge was called with correct args
            mock_merge.assert_called_once_with("base_commit", "other_commit")


# Test for the merge command with invalid base commit
@pytest.mark.cli
def test_merge_command_invalid_base(temp_dir: pathlib.Path):
    """
    Test the merge command functionality with invalid base commit.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Mock the validate_commit_reference function to return False for base commit
    with patch("clony.cli.validate_commit_reference") as mock_validate:
        # Configure the mock to return False for the first call (base commit)
        # and True for the second call (other commit) if it happens
        mock_validate.side_effect = [False, True]

        # Run the merge command
        result = runner.invoke(cli, ["merge", "invalid_base", "other_commit"])

        # Assert that the command exits with code 1 due to invalid base commit
        assert result.exit_code == 1

        # Assert validation function was called with base commit
        mock_validate.assert_called_with("invalid_base")


# Test for the merge command with invalid other commit
@pytest.mark.cli
def test_merge_command_invalid_other(temp_dir: pathlib.Path):
    """
    Test the merge command functionality with invalid other commit.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Mock the validate_commit_reference function to return patterns
    with patch("clony.cli.validate_commit_reference") as mock_validate:
        # Configure the mock to return True for the first call (base commit)
        # and False for the second call (other commit)
        mock_validate.side_effect = [True, False]

        # Run the merge command
        result = runner.invoke(cli, ["merge", "base_commit", "invalid_other"])

        # Assert that the command exits with code 1 due to invalid other commit
        assert result.exit_code == 1

        # Assert validation function was called with both commits
        assert mock_validate.call_count == 2
        mock_validate.assert_any_call("base_commit")
        mock_validate.assert_any_call("invalid_other")


# Test for the merge command with exception
@pytest.mark.cli
def test_merge_command_exception(temp_dir: pathlib.Path):
    """
    Test the merge command functionality when an exception occurs.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Mock the validate_commit_reference function to return True
    with patch("clony.cli.validate_commit_reference", return_value=True):
        # Mock the perform_merge function to raise an exception
        with patch(
            "clony.cli.perform_merge", side_effect=Exception("Test exception")
        ) as mock_merge:
            # Run the merge command
            result = runner.invoke(cli, ["merge", "base_commit", "other_commit"])

            # Assert that the command exits with code 1 due to the exception
            assert result.exit_code == 1

            # Assert that perform_merge was called with correct args
            mock_merge.assert_called_once_with("base_commit", "other_commit")
