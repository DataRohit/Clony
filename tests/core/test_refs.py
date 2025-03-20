"""
Tests for the Git references functionality.

This module contains tests for the refs module, including HEAD and branch references.
"""

# Standard library imports
import pathlib
import shutil
import tempfile
from typing import Generator
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from clony.core.refs import (
    create_branch,
    delete_branch,
    get_current_branch,
    get_head_commit,
    get_head_ref,
    get_ref_hash,
    list_branches,
    update_ref,
)
from clony.core.repository import Repository


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


# Test for get_head_ref function
@pytest.mark.unit
def test_get_head_ref(temp_dir: pathlib.Path):
    """
    Test the get_head_ref function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Get the HEAD reference
    head_ref = get_head_ref(temp_dir)

    # Assert that the HEAD reference is correct
    assert head_ref == "refs/heads/main"

    # Test with a direct commit hash
    head_file = temp_dir / ".git" / "HEAD"
    commit_hash = "1234567890abcdef1234567890abcdef12345678"
    with open(head_file, "w") as f:
        f.write(commit_hash)

    # Get the HEAD reference again
    head_ref = get_head_ref(temp_dir)

    # Assert that the HEAD reference is the commit hash
    assert head_ref == commit_hash


# Test for get_current_branch function
@pytest.mark.unit
def test_get_current_branch(temp_dir: pathlib.Path):
    """
    Test the get_current_branch function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Get the current branch
    branch = get_current_branch(temp_dir)

    # Assert that the current branch is "main"
    assert branch == "main"

    # Test with a direct commit hash (detached HEAD)
    head_file = temp_dir / ".git" / "HEAD"
    commit_hash = "1234567890abcdef1234567890abcdef12345678"
    with open(head_file, "w") as f:
        f.write(commit_hash)

    # Get the current branch again
    branch = get_current_branch(temp_dir)

    # Assert that the current branch is None (detached HEAD)
    assert branch is None


# Test for update_ref function
@pytest.mark.unit
def test_update_ref(temp_dir: pathlib.Path):
    """
    Test the update_ref function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Define a reference and commit hash
    ref_name = "refs/heads/test-branch"
    commit_hash = "1234567890abcdef1234567890abcdef12345678"

    # Update the reference
    update_ref(temp_dir, ref_name, commit_hash)

    # Assert that the reference file was created
    ref_file = temp_dir / ".git" / ref_name
    assert ref_file.exists()

    # Assert that the reference file contains the commit hash
    with open(ref_file, "r") as f:
        assert f.read().strip() == commit_hash


# Test for get_ref_hash function
@pytest.mark.unit
def test_get_ref_hash(temp_dir: pathlib.Path):
    """
    Test the get_ref_hash function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Define a reference and commit hash
    ref_name = "refs/heads/test-branch"
    commit_hash = "1234567890abcdef1234567890abcdef12345678"

    # Update the reference
    update_ref(temp_dir, ref_name, commit_hash)

    # Get the commit hash for the reference
    ref_hash = get_ref_hash(temp_dir, ref_name)

    # Assert that the returned hash matches the expected hash
    assert ref_hash == commit_hash

    # Test with a non-existent reference
    ref_hash = get_ref_hash(temp_dir, "refs/heads/non-existent")

    # Assert that the returned hash is None
    assert ref_hash is None


# Test for get_head_commit function
@pytest.mark.unit
def test_get_head_commit(temp_dir: pathlib.Path):
    """
    Test the get_head_commit function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Define a commit hash
    commit_hash = "1234567890abcdef1234567890abcdef12345678"

    # Update the main branch reference
    update_ref(temp_dir, "refs/heads/main", commit_hash)

    # Get the HEAD commit
    head_commit = get_head_commit(temp_dir)

    # Assert that the returned commit hash matches the expected hash
    assert head_commit == commit_hash

    # Test with a direct commit hash
    head_file = temp_dir / ".git" / "HEAD"
    with open(head_file, "w") as f:
        f.write(commit_hash)

    # Get the HEAD commit again
    head_commit = get_head_commit(temp_dir)

    # Assert that the returned commit hash matches the expected hash
    assert head_commit == commit_hash


# Test for create_branch function
@pytest.mark.unit
def test_create_branch(temp_dir: pathlib.Path):
    """
    Test the create_branch function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Define a commit hash
    commit_hash = "1234567890abcdef1234567890abcdef12345678"

    # Update the main branch reference
    update_ref(temp_dir, "refs/heads/main", commit_hash)

    # Create a new branch
    result = create_branch(temp_dir, "test-branch")

    # Assert that branch creation was successful
    assert result is True

    # Assert that the branch reference file was created
    branch_file = temp_dir / ".git" / "refs" / "heads" / "test-branch"
    assert branch_file.exists()

    # Assert that the branch reference contains the commit hash
    with open(branch_file, "r") as f:
        assert f.read().strip() == commit_hash

    # Test creating a branch at a specific commit
    new_commit = "9876543210abcdef9876543210abcdef98765432"
    result = create_branch(temp_dir, "specific-commit", new_commit)

    # Assert that branch creation was successful
    assert result is True

    # Assert that the branch reference file was created
    branch_file = temp_dir / ".git" / "refs" / "heads" / "specific-commit"
    assert branch_file.exists()

    # Assert that the branch reference contains the specified commit hash
    with open(branch_file, "r") as f:
        assert f.read().strip() == new_commit

    # Test creating a branch that already exists
    result = create_branch(temp_dir, "test-branch")

    # Assert that branch creation failed
    assert result is False

    # Test creating a branch with invalid name
    result = create_branch(temp_dir, "invalid/branch")

    # Assert that branch creation failed
    assert result is False

    # Test with invalid HEAD
    # Remove the HEAD file
    head_file = temp_dir / ".git" / "HEAD"
    head_file.unlink()
    with open(head_file, "w") as f:
        f.write("ref: refs/heads/non-existent")

    # Try to create a branch with the invalid HEAD
    result = create_branch(temp_dir, "invalid-head-branch")

    # Assert that branch creation failed
    assert result is False

    # Test exception handling in create_branch
    with patch("clony.core.refs.update_ref", side_effect=Exception("Test exception")):
        result = create_branch(temp_dir, "exception-branch", commit_hash)
        assert result is False


# Test for list_branches function
@pytest.mark.unit
def test_list_branches(temp_dir: pathlib.Path):
    """
    Test the list_branches function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Define a commit hash
    commit_hash = "1234567890abcdef1234567890abcdef12345678"

    # Update the main branch reference
    update_ref(temp_dir, "refs/heads/main", commit_hash)

    # Create additional branches
    update_ref(temp_dir, "refs/heads/branch1", commit_hash)
    update_ref(temp_dir, "refs/heads/branch2", commit_hash)

    # List branches
    branches = list_branches(temp_dir)

    # Assert that all branches are listed
    assert len(branches) == 3
    assert "main" in branches
    assert "branch1" in branches
    assert "branch2" in branches

    # Test with no branches directory
    no_branches_dir = temp_dir / "empty"
    no_branches_dir.mkdir()

    # Create the .git directory structure
    (no_branches_dir / ".git").mkdir()

    # List branches in the empty directory
    branches = list_branches(no_branches_dir)

    # Assert that no branches are listed
    assert branches == []


# Test for delete_branch function
@pytest.mark.unit
def test_delete_branch(temp_dir: pathlib.Path):
    """
    Test the delete_branch function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Define a commit hash
    commit_hash = "1234567890abcdef1234567890abcdef12345678"

    # Update the main branch reference
    update_ref(temp_dir, "refs/heads/main", commit_hash)

    # Create additional branches
    update_ref(temp_dir, "refs/heads/branch-to-delete", commit_hash)

    # Delete a branch
    result = delete_branch(temp_dir, "branch-to-delete")

    # Assert that branch deletion was successful
    assert result is True

    # Assert that the branch reference file was deleted
    branch_file = temp_dir / ".git" / "refs" / "heads" / "branch-to-delete"
    assert not branch_file.exists()

    # Test deleting a non-existent branch
    result = delete_branch(temp_dir, "non-existent-branch")

    # Assert that branch deletion failed
    assert result is False

    # Test deleting the current branch
    result = delete_branch(temp_dir, "main")

    # Assert that branch deletion failed
    assert result is False

    # Test deleting the current branch with force option
    result = delete_branch(temp_dir, "main", force=True)

    # Assert that branch deletion was successful
    assert result is True

    # Assert that the branch reference file was deleted
    branch_file = temp_dir / ".git" / "refs" / "heads" / "main"
    assert not branch_file.exists()

    # Test exception handling in delete_branch
    # Create a new branch for testing exceptions
    update_ref(temp_dir, "refs/heads/exception-branch", commit_hash)

    # Test with an exception when trying to unlink the file
    with patch("pathlib.Path.unlink", side_effect=Exception("Test exception")):
        result = delete_branch(temp_dir, "exception-branch")
        assert result is False
