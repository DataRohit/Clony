"""
Tests for the Git references functionality.

This module contains tests for the refs module, including HEAD and branch references.
"""

# Standard library imports
import pathlib
import shutil
import tempfile
from typing import Generator

# Third-party imports
import pytest

# Local imports
from clony.core.refs import (
    get_current_branch,
    get_head_commit,
    get_head_ref,
    get_ref_hash,
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
