"""
Tests for the reset command in the Clony CLI.

This module contains tests for the reset command in the Clony CLI.
"""

# Standard library imports
import os
from unittest.mock import patch

# Third-party imports
import pytest
from click.testing import CliRunner

# Local imports
from clony.cli import cli
from clony.core.refs import get_head_commit
from clony.core.repository import Repository
from clony.internals.commit import make_commit
from clony.internals.staging import stage_file


# Fixture for a repository with commits
@pytest.fixture
def repo_with_commits(tmp_path):
    """
    Create a repository with multiple commits for testing reset.

    This fixture sets up a test repository with three commits,
    each with different content, for testing reset functionality.
    """

    # Create a repository
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    repo = Repository(str(repo_path))
    repo.init()

    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(repo_path)

    # Create a file and make the first commit
    first_file = repo_path / "first.txt"
    first_file.write_text("First file content")
    stage_file(str(first_file))
    first_commit = make_commit("First commit", "Test User", "test@example.com")

    # Create a second file and make the second commit
    second_file = repo_path / "second.txt"
    second_file.write_text("Second file content")
    stage_file(str(second_file))
    second_commit = make_commit("Second commit", "Test User", "test@example.com")

    # Create a third file and make the third commit
    third_file = repo_path / "third.txt"
    third_file.write_text("Third file content")
    stage_file(str(third_file))
    third_commit = make_commit("Third commit", "Test User", "test@example.com")

    # Return to the original directory
    os.chdir(original_dir)

    # Return the repository path and commit hashes
    return {
        "repo_path": repo_path,
        "first_commit": first_commit,
        "second_commit": second_commit,
        "third_commit": third_commit,
    }


# Test soft reset CLI command with tabular output
@pytest.mark.cli
def test_reset_soft_cli(repo_with_commits):
    """
    Test the soft reset mode via CLI with tabular output.

    This test verifies that the reset command with soft mode displays
    the reset information in a tabular format.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    first_commit = repo_with_commits["first_commit"]
    third_commit = repo_with_commits["third_commit"]

    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(repo_path)

    try:
        # Verify we're at the third commit
        assert get_head_commit(repo_path) == third_commit

        # Mock the display_reset_info function to verify it's called
        with patch("clony.internals.reset.display_reset_info") as mock_display:
            # Run the reset command with soft mode
            runner = CliRunner()
            result = runner.invoke(
                cli, ["reset", "--soft", first_commit], catch_exceptions=False
            )

            # Check the command succeeded
            assert result.exit_code == 0

            # Verify display_reset_info was called with the correct arguments
            mock_display.assert_called_once()
            assert mock_display.call_args[0][0] == first_commit  # commit_hash
            assert mock_display.call_args[0][1] == "soft"  # mode
    finally:
        os.chdir(original_dir)


# Test mixed reset CLI command with tabular output
@pytest.mark.cli
def test_reset_mixed_cli(repo_with_commits):
    """
    Test the mixed reset mode via CLI with tabular output.

    This test verifies that the reset command with mixed mode displays
    the reset information in a tabular format.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    second_commit = repo_with_commits["second_commit"]
    third_commit = repo_with_commits["third_commit"]

    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(repo_path)

    try:
        # Verify we're at the third commit
        assert get_head_commit(repo_path) == third_commit

        # Mock the display_reset_info function to verify it's called
        with patch("clony.internals.reset.display_reset_info") as mock_display:
            # Run the reset command with mixed mode (default)
            runner = CliRunner()
            result = runner.invoke(
                cli, ["reset", second_commit], catch_exceptions=False
            )

            # Check the command succeeded
            assert result.exit_code == 0

            # Verify display_reset_info was called with the correct arguments
            mock_display.assert_called_once()
            assert mock_display.call_args[0][0] == second_commit  # commit_hash
            assert mock_display.call_args[0][1] == "mixed"  # mode
    finally:
        os.chdir(original_dir)


# Test hard reset CLI command with tabular output
@pytest.mark.cli
def test_reset_hard_cli(repo_with_commits):
    """
    Test the hard reset mode via CLI with tabular output.

    This test verifies that the reset command with hard mode displays
    the reset information in a tabular format.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    first_commit = repo_with_commits["first_commit"]
    third_commit = repo_with_commits["third_commit"]

    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(repo_path)

    try:
        # Verify we're at the third commit
        assert get_head_commit(repo_path) == third_commit

        # Mock the display_reset_info function to verify it's called
        with patch("clony.internals.reset.display_reset_info") as mock_display:
            # Run the reset command with hard mode
            runner = CliRunner()
            result = runner.invoke(
                cli, ["reset", "--hard", first_commit], catch_exceptions=False
            )

            # Check the command succeeded
            assert result.exit_code == 0

            # Verify display_reset_info was called with the correct arguments
            mock_display.assert_called_once()
            assert mock_display.call_args[0][0] == first_commit  # commit_hash
            assert mock_display.call_args[0][1] == "hard"  # mode
    finally:
        os.chdir(original_dir)


# Test reset with invalid commit reference via CLI
@pytest.mark.cli
def test_reset_invalid_commit_cli(repo_with_commits):
    """
    Test reset with an invalid commit reference via CLI.
    """

    # Get the repository path
    repo_path = repo_with_commits["repo_path"]

    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(repo_path)

    try:
        # Run the reset command with an invalid commit reference
        runner = CliRunner()
        result = runner.invoke(cli, ["reset", "invalid-commit"], catch_exceptions=False)

        # Check the command failed
        assert result.exit_code == 1
        assert "Invalid commit reference: invalid-commit" in result.output
    finally:
        os.chdir(original_dir)


# Test reset with explicit mixed mode
@pytest.mark.cli
def test_reset_explicit_mixed_cli(repo_with_commits):
    """
    Test reset with explicit mixed mode via CLI.

    This test verifies that the reset command with explicit mixed mode displays
    the reset information in a tabular format.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    second_commit = repo_with_commits["second_commit"]
    third_commit = repo_with_commits["third_commit"]

    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(repo_path)

    try:
        # Verify we're at the third commit
        assert get_head_commit(repo_path) == third_commit

        # Mock the display_reset_info function to verify it's called
        with patch("clony.internals.reset.display_reset_info") as mock_display:
            # Run the reset command with explicit mixed mode
            runner = CliRunner()
            result = runner.invoke(
                cli, ["reset", "--mixed", second_commit], catch_exceptions=False
            )

            # Check the command succeeded
            assert result.exit_code == 0

            # Verify display_reset_info was called with the correct arguments
            mock_display.assert_called_once()
            assert mock_display.call_args[0][0] == second_commit  # commit_hash
            assert mock_display.call_args[0][1] == "mixed"  # mode
    finally:
        os.chdir(original_dir)


# Test reset with multiple mode flags (should use the first one)
@pytest.mark.cli
def test_reset_multiple_modes_cli(repo_with_commits):
    """
    Test reset with multiple mode flags via CLI.

    This test verifies that when multiple mode flags are provided,
    the first one (in this case soft) is used.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    first_commit = repo_with_commits["first_commit"]
    third_commit = repo_with_commits["third_commit"]

    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(repo_path)

    try:
        # Verify we're at the third commit
        assert get_head_commit(repo_path) == third_commit

        # Mock the display_reset_info function to verify it's called
        with patch("clony.internals.reset.display_reset_info") as mock_display:
            # Run the reset command with multiple mode flags
            # The first one (soft) should be used
            runner = CliRunner()
            result = runner.invoke(
                cli, ["reset", "--soft", "--hard", first_commit], catch_exceptions=False
            )

            # Check the command succeeded
            assert result.exit_code == 0

            # Verify display_reset_info was called with the correct arguments
            mock_display.assert_called_once()
            assert mock_display.call_args[0][0] == first_commit  # commit_hash
            assert mock_display.call_args[0][1] == "soft"  # mode
    finally:
        os.chdir(original_dir)


# Test exception handling in reset command
@pytest.mark.cli
def test_reset_exception():
    """
    Test error handling in the reset command.

    This test verifies that when an exception is raised during reset,
    it's properly caught and reported.
    """
    # Set up the runner
    runner = CliRunner()

    # Mock reset_head to raise an exception
    with (
        patch("clony.cli.reset_head") as mock_reset,
        patch("clony.cli.logger.error") as mock_error,
    ):
        # Set up the mock to raise an exception
        mock_reset.side_effect = Exception("Test error")

        # Run the command
        result = runner.invoke(cli, ["reset", "HEAD~1"], catch_exceptions=False)

        # Check the command failed
        assert result.exit_code == 1

        # Verify logger.error was called
        mock_error.assert_called_once_with("Error performing reset: Test error")
