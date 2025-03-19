"""
Tests for the blobs command in the CLI.

This module contains tests for the blobs command functionality.
"""

# Standard library imports
import pathlib
import sys
from unittest.mock import patch

# Third-party imports
import pytest
from click.testing import CliRunner

# Local imports
from clony.cli import blobs
from clony.core.objects import (
    create_blob_object,
    create_commit_object,
    create_tree_object,
)
from clony.core.repository import Repository


# Test fixture for creating a repository with a commit
@pytest.fixture
def repo_with_commit(tmp_path: pathlib.Path):
    """
    Create a repository with a commit containing multiple files.

    Args:
        tmp_path (pathlib.Path): Temporary directory path.

    Returns:
        dict: Dictionary containing repository information.
    """

    # Initialize a repository
    repo = Repository(str(tmp_path))
    repo.init()

    # Create test files
    test_file1 = tmp_path / "file1.txt"
    test_file1.write_text("file1 content")
    test_file2 = tmp_path / "file2.txt"
    test_file2.write_text("file2 content")

    # Create a subdirectory with a file
    test_subdir = tmp_path / "subdir"
    test_subdir.mkdir()
    test_file3 = test_subdir / "file3.txt"
    test_file3.write_text("file3 content")

    # Create blob objects
    _ = create_blob_object(tmp_path, test_file1)
    _ = create_blob_object(tmp_path, test_file2)
    _ = create_blob_object(tmp_path, test_file3)

    # Create a tree object
    tree_hash = create_tree_object(tmp_path, tmp_path)

    # Create a commit
    commit_hash = create_commit_object(
        tmp_path, tree_hash, None, "Test Author", "test@example.com", "Test commit"
    )

    # Return repository information
    return {
        "repo_path": tmp_path,
        "commit_hash": commit_hash,
        "tree_hash": tree_hash,
        "files": [test_file1, test_file2, test_file3],
    }


# Test for blobs command with valid commit
@pytest.mark.unit
def test_blobs_command_valid_commit(repo_with_commit):
    """
    Test the blobs command with a valid commit hash.
    """

    # Get the repository information
    repo_path = repo_with_commit["repo_path"]
    commit_hash = repo_with_commit["commit_hash"]

    # Create a CLI runner
    runner = CliRunner()

    # Mock the current working directory
    with patch("pathlib.Path.cwd") as mock_cwd:
        mock_cwd.return_value = repo_path

        # Run the blobs command
        result = runner.invoke(blobs, [commit_hash], catch_exceptions=False)

        # Assert that the command was successful
        assert result.exit_code == 0

        # Assert that the output contains expected information
        assert "Blob Hashes in Commit" in result.output
        assert "file1.txt" in result.output
        assert "file2.txt" in result.output
        assert "subdir/file3.txt" in result.output


# Test for blobs command with invalid commit
@pytest.mark.unit
def test_blobs_command_invalid_commit(repo_with_commit, caplog):
    """
    Test the blobs command with an invalid commit hash.
    """

    # Get the repository path
    repo_path = repo_with_commit["repo_path"]

    # Create a CLI runner
    runner = CliRunner()

    # Mock the current working directory
    with patch("pathlib.Path.cwd") as mock_cwd:
        mock_cwd.return_value = repo_path

        # Run the blobs command with an invalid commit hash
        result = runner.invoke(blobs, ["invalid_commit"], catch_exceptions=False)

        # Assert that the command failed
        assert result.exit_code == 1
        assert "Invalid commit reference: invalid_commit" in caplog.text


# Test for blobs command with non-commit object
@pytest.mark.unit
def test_blobs_command_non_commit_object(repo_with_commit, caplog):
    """
    Test the blobs command with a non-commit object hash.
    """

    # Get the repository information
    repo_path = repo_with_commit["repo_path"]
    tree_hash = repo_with_commit["tree_hash"]

    # Create a CLI runner
    runner = CliRunner()

    # Mock the current working directory
    with patch("pathlib.Path.cwd") as mock_cwd:
        mock_cwd.return_value = repo_path

        # Run the blobs command with a tree hash
        result = runner.invoke(blobs, [tree_hash], catch_exceptions=False)

        # Assert that the command failed
        assert result.exit_code == 1
        assert f"Object {tree_hash} is not a commit" in caplog.text


# Test for blobs command with commit having no tree
@pytest.mark.unit
def test_blobs_command_commit_no_tree(repo_with_commit, monkeypatch, caplog):
    """
    Test the blobs command with a commit that has no tree.
    """

    # Get the repository information
    repo_path = repo_with_commit["repo_path"]
    commit_hash = repo_with_commit["commit_hash"]

    # Create a CLI runner
    runner = CliRunner()

    # Mock parse_commit_object to return a commit info without tree
    def mock_parse_commit(*args, **kwargs):
        return {"message": "Test commit"}

    monkeypatch.setattr("clony.cli.parse_commit_object", mock_parse_commit)

    # Mock the current working directory
    with patch("pathlib.Path.cwd") as mock_cwd:
        mock_cwd.return_value = repo_path

        # Run the blobs command
        result = runner.invoke(blobs, [commit_hash], catch_exceptions=False)

        # Assert that the command failed
        assert result.exit_code == 1
        assert "No tree found in commit" in caplog.text


# Test for blobs command with invalid tree object
@pytest.mark.unit
def test_blobs_command_invalid_tree(repo_with_commit, monkeypatch):
    """
    Test the blobs command with an invalid tree object.
    """

    # Get the repository information
    repo_path = repo_with_commit["repo_path"]
    commit_hash = repo_with_commit["commit_hash"]

    # Create a CLI runner
    runner = CliRunner()

    # Mock read_git_object to return a non-tree object for the tree hash
    original_read_git_object = sys.modules["clony.core.diff"].read_git_object
    call_count = 0

    def mock_read_git_object(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # First call for commit object
            return original_read_git_object(*args, **kwargs)
        return "blob", b""  # Second call for tree object

    monkeypatch.setattr("clony.cli.read_git_object", mock_read_git_object)

    # Mock the current working directory
    with patch("pathlib.Path.cwd") as mock_cwd:
        mock_cwd.return_value = repo_path

        # Run the blobs command
        result = runner.invoke(blobs, [commit_hash], catch_exceptions=False)

        # Assert that the command was successful (empty table is valid)
        assert result.exit_code == 0
        assert "Blob Hashes in Commit" in result.output


# Test for blobs command with exception during processing
@pytest.mark.unit
def test_blobs_command_processing_error(repo_with_commit, monkeypatch, caplog):
    """
    Test the blobs command when an exception occurs during processing.
    """

    # Get the repository information
    repo_path = repo_with_commit["repo_path"]
    commit_hash = repo_with_commit["commit_hash"]

    # Create a CLI runner
    runner = CliRunner()

    # Mock read_git_object to raise an exception
    def mock_read_git_object(*args, **kwargs):
        raise Exception("Test error")

    monkeypatch.setattr("clony.cli.read_git_object", mock_read_git_object)

    # Mock the current working directory
    with patch("pathlib.Path.cwd") as mock_cwd:
        mock_cwd.return_value = repo_path

        # Run the blobs command
        result = runner.invoke(blobs, [commit_hash], catch_exceptions=False)

        # Assert that the command failed
        assert result.exit_code == 1
        assert "Error retrieving blob hashes: Test error" in caplog.text
