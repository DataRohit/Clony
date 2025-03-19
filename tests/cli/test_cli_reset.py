"""
Tests for the reset command in the Clony CLI.

This module contains tests for the reset command in the Clony CLI.
"""

# Standard library imports
import os

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
    """

    # Create a repository
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    repo = Repository(str(repo_path))
    repo.init()

    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(repo_path)

    try:
        # Create a file and make an initial commit
        with open("file1.txt", "w") as f:
            f.write("Initial content")

        # Stage and commit the file
        stage_file("file1.txt")
        first_commit = make_commit("Initial commit", "Test User", "test@example.com")

        # Modify the file and make a second commit
        with open("file1.txt", "w") as f:
            f.write("Modified content")

        # Stage and commit the file
        stage_file("file1.txt")
        second_commit = make_commit("Second commit", "Test User", "test@example.com")

        # Create a new file and make a third commit
        with open("file2.txt", "w") as f:
            f.write("New file content")

        # Stage and commit the file
        stage_file("file2.txt")
        third_commit = make_commit("Third commit", "Test User", "test@example.com")

        # Return the repository path and commit hashes
        return {
            "repo_path": repo_path,
            "first_commit": first_commit,
            "second_commit": second_commit,
            "third_commit": third_commit,
        }
    finally:
        # Change back to the original directory
        os.chdir(original_dir)


# Test soft reset CLI command
@pytest.mark.cli
def test_reset_soft_cli(repo_with_commits):
    """
    Test the soft reset mode via CLI.
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

        # Run the reset command with soft mode
        runner = CliRunner()
        result = runner.invoke(
            cli, ["reset", "--soft", first_commit], catch_exceptions=False
        )

        # Check the command succeeded
        assert result.exit_code == 0
        assert f"Reset HEAD to {first_commit} (soft mode)" in result.output
    finally:
        os.chdir(original_dir)


# Test mixed reset CLI command
@pytest.mark.cli
def test_reset_mixed_cli(repo_with_commits):
    """
    Test the mixed reset mode via CLI.
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

        # Run the reset command with mixed mode (default)
        runner = CliRunner()
        result = runner.invoke(cli, ["reset", second_commit], catch_exceptions=False)

        # Check the command succeeded
        assert result.exit_code == 0
        assert f"Reset HEAD to {second_commit} (mixed mode)" in result.output
    finally:
        os.chdir(original_dir)


# Test hard reset CLI command
@pytest.mark.cli
def test_reset_hard_cli(repo_with_commits):
    """
    Test the hard reset mode via CLI.
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

        # Run the reset command with hard mode
        runner = CliRunner()
        result = runner.invoke(
            cli, ["reset", "--hard", first_commit], catch_exceptions=False
        )

        # Check the command succeeded
        assert result.exit_code == 0
        assert f"Reset HEAD to {first_commit} (hard mode)" in result.output
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

        # Run the reset command with explicit mixed mode
        runner = CliRunner()
        result = runner.invoke(
            cli, ["reset", "--mixed", second_commit], catch_exceptions=False
        )

        # Check the command succeeded
        assert result.exit_code == 0
        assert f"Reset HEAD to {second_commit} (mixed mode)" in result.output
    finally:
        os.chdir(original_dir)


# Test reset with multiple mode flags (should use the first one)
@pytest.mark.cli
def test_reset_multiple_modes_cli(repo_with_commits):
    """
    Test reset with multiple mode flags via CLI.
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

        # Run the reset command with multiple mode flags
        # The first one (soft) should be used
        runner = CliRunner()
        result = runner.invoke(
            cli, ["reset", "--soft", "--hard", first_commit], catch_exceptions=False
        )

        # Check the command succeeded
        assert result.exit_code == 0
        assert f"Reset HEAD to {first_commit} (soft mode)" in result.output
    finally:
        os.chdir(original_dir)
