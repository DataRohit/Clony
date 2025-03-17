"""
Tests for the reset functionality in the internals module.

This module contains tests for the reset functionality in the Clony internals module.
"""

# Standard library imports
import os
from pathlib import Path

# Third-party imports
import pytest

# Local imports
from clony.core.refs import get_head_commit
from clony.core.repository import Repository
from clony.internals.commit import make_commit
from clony.internals.reset import (
    reset_head,
    update_head_to_commit,
    update_index_to_commit,
    update_working_dir_to_commit,
    validate_commit_reference,
)
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


# Test validate_commit_reference function
def test_validate_commit_reference(repo_with_commits):
    """
    Test the validate_commit_reference function.
    """
    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    first_commit = repo_with_commits["first_commit"]

    # Test with a valid commit hash
    assert validate_commit_reference(repo_path, first_commit) == first_commit

    # Test with a shortened commit hash
    shortened_hash = first_commit[:7]  # First 7 characters
    assert validate_commit_reference(repo_path, shortened_hash) == first_commit

    # Test with a very short commit hash (should still work if unique)
    very_short_hash = first_commit[:4]  # First 4 characters
    assert validate_commit_reference(repo_path, very_short_hash) == first_commit

    # Test with an ambiguous shortened hash (create a similar hash)
    # This is simulated by creating a mock directory structure
    prefix = first_commit[:2]
    objects_dir = repo_path / ".git" / "objects" / prefix
    objects_dir.mkdir(parents=True, exist_ok=True)

    # Create a file with a similar name to simulate ambiguity
    similar_hash = first_commit[2:6] + "abcdef" * 6  # Different but starts the same
    similar_file = objects_dir / similar_hash
    if not similar_file.exists():
        similar_file.touch()

    # Now test with an ambiguous prefix
    ambiguous_prefix = first_commit[:4]
    assert validate_commit_reference(repo_path, ambiguous_prefix) is None

    # Test with a branch name
    # First, create a branch
    branch_ref_file = repo_path / ".git" / "refs" / "heads" / "test-branch"
    branch_ref_file.parent.mkdir(parents=True, exist_ok=True)
    with open(branch_ref_file, "w") as f:
        f.write(first_commit + "\n")

    assert validate_commit_reference(repo_path, "test-branch") == first_commit

    # Test with a tag name
    # First, create a tag
    tag_ref_file = repo_path / ".git" / "refs" / "tags" / "test-tag"
    tag_ref_file.parent.mkdir(parents=True, exist_ok=True)
    with open(tag_ref_file, "w") as f:
        f.write(first_commit + "\n")

    # Validate the commit reference
    assert validate_commit_reference(repo_path, "test-tag") == first_commit

    # Test with an invalid reference
    assert validate_commit_reference(repo_path, "invalid-ref") is None

    # Test with an invalid commit hash
    invalid_hash = "0" * 40
    assert validate_commit_reference(repo_path, invalid_hash) is None

    # Test with a shortened hash that doesn't exist
    non_existent_short = "1234"
    assert validate_commit_reference(repo_path, non_existent_short) is None


# Test update_head_to_commit function
def test_update_head_to_commit(repo_with_commits):
    """
    Test the update_head_to_commit function.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    first_commit = repo_with_commits["first_commit"]
    second_commit = repo_with_commits["second_commit"]

    # Test updating HEAD when it's a reference
    assert update_head_to_commit(repo_path, first_commit) is True
    assert get_head_commit(repo_path) == first_commit

    # Test updating HEAD when it's detached
    # First, detach HEAD
    head_file = repo_path / ".git" / "HEAD"
    with open(head_file, "w") as f:
        f.write(first_commit + "\n")

    # Now update the detached HEAD
    assert update_head_to_commit(repo_path, second_commit) is True
    assert get_head_commit(repo_path) == second_commit


# Test update_index_to_commit function
def test_update_index_to_commit(repo_with_commits):
    """
    Test the update_index_to_commit function.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    first_commit = repo_with_commits["first_commit"]

    # Test updating the index
    assert update_index_to_commit(repo_path, first_commit) is True


# Test update_working_dir_to_commit function
def test_update_working_dir_to_commit(repo_with_commits):
    """
    Test the update_working_dir_to_commit function.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    first_commit = repo_with_commits["first_commit"]

    # Test updating the working directory
    assert update_working_dir_to_commit(repo_path, first_commit) is True


# Test reset_head function directly
def test_reset_head_direct(repo_with_commits):
    """
    Test the reset_head function directly.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    first_commit = repo_with_commits["first_commit"]
    third_commit = repo_with_commits["third_commit"]

    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(repo_path)

    try:
        # Test soft reset
        assert reset_head(first_commit, "soft") is True
        assert get_head_commit(repo_path) == first_commit

        # Test mixed reset
        assert reset_head(third_commit, "mixed") is True
        assert get_head_commit(repo_path) == third_commit

        # Test hard reset
        assert reset_head(first_commit, "hard") is True
        assert get_head_commit(repo_path) == first_commit

        # Test with invalid commit reference
        assert reset_head("invalid-ref") is False

        # Test when not in a Git repository
        os.chdir(Path(repo_path).parent)
        assert reset_head(first_commit) is False

        # Test with explicit repo_path parameter
        assert reset_head(third_commit, repo_path=repo_path) is True
        assert get_head_commit(repo_path) == third_commit

        # Test with explicit repo_path parameter and mode
        assert reset_head(first_commit, "hard", repo_path=repo_path) is True
        assert get_head_commit(repo_path) == first_commit
    finally:
        # Change back to the original directory
        os.chdir(original_dir)


# Test reset_head function with failing update_head_to_commit
def test_reset_head_update_head_failure(repo_with_commits, monkeypatch):
    """
    Test the reset_head function when update_head_to_commit fails.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    first_commit = repo_with_commits["first_commit"]

    # Mock update_head_to_commit to return False
    def mock_update_head_to_commit(*args, **kwargs):
        return False

    # Apply the monkeypatch
    monkeypatch.setattr(
        "clony.internals.reset.update_head_to_commit", mock_update_head_to_commit
    )

    # Test reset_head with the mocked function
    assert reset_head(first_commit, repo_path=repo_path) is False


# Test reset_head function with failing update_index_to_commit
def test_reset_head_update_index_failure(repo_with_commits, monkeypatch):
    """
    Test the reset_head function when update_index_to_commit fails.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    first_commit = repo_with_commits["first_commit"]

    # Mock update_index_to_commit to return False
    def mock_update_index_to_commit(*args, **kwargs):
        return False

    # Apply the monkeypatch
    monkeypatch.setattr(
        "clony.internals.reset.update_index_to_commit", mock_update_index_to_commit
    )

    # Test reset_head with the mocked function
    assert reset_head(first_commit, "mixed", repo_path=repo_path) is False


# Test reset_head function with failing update_working_dir_to_commit
def test_reset_head_update_working_dir_failure(repo_with_commits, monkeypatch):
    """
    Test the reset_head function when update_working_dir_to_commit fails.
    """

    # Get the repository path and commit hashes
    repo_path = repo_with_commits["repo_path"]
    first_commit = repo_with_commits["first_commit"]

    # Mock update_working_dir_to_commit to return False
    def mock_update_working_dir_to_commit(*args, **kwargs):
        return False

    # Apply the monkeypatch
    monkeypatch.setattr(
        "clony.internals.reset.update_working_dir_to_commit",
        mock_update_working_dir_to_commit,
    )

    # Test reset_head with the mocked function
    assert reset_head(first_commit, "hard", repo_path=repo_path) is False
