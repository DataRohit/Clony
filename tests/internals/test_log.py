"""
Tests for the log functionality.

This module contains tests for the log module, including reading Git objects,
parsing commit objects, and displaying commit history.
"""

# Standard library imports
import pathlib
import shutil
import tempfile
import zlib
from typing import Generator
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from clony.core.objects import create_commit_object, write_object_file
from clony.core.refs import update_ref
from clony.internals.log import (
    display_commit_logs,
    format_timestamp,
    get_commit_logs,
    parse_commit_object,
    read_git_object,
)


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

    # Create the .git directory structure
    git_dir = temp_path / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)
    (git_dir / "objects").mkdir(parents=True, exist_ok=True)
    (git_dir / "refs" / "heads").mkdir(parents=True, exist_ok=True)

    # Initialize HEAD to point to main branch
    with open(git_dir / "HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")

    # Yield the temporary directory path
    yield temp_path

    # Clean up the temporary directory
    shutil.rmtree(temp_path)


# Test for read_git_object function
@pytest.mark.unit
def test_read_git_object(temp_dir: pathlib.Path):
    """
    Test the read_git_object function.
    """

    # Create a test object
    content = b"test content"
    object_type = "blob"
    header = f"{object_type} {len(content)}\0".encode()
    store_content = header + content

    # Calculate the SHA-1 hash
    import hashlib

    # Calculate the SHA-1 hash
    sha1_hash = hashlib.sha1(store_content).hexdigest()

    # Create the object directory
    object_dir = temp_dir / ".git" / "objects"
    object_subdir = object_dir / sha1_hash[:2]
    object_subdir.mkdir(parents=True, exist_ok=True)
    object_file_path = object_subdir / sha1_hash[2:]

    # Write the compressed content to the object file
    with open(object_file_path, "wb") as f:
        f.write(zlib.compress(store_content))

    # Read the object
    read_type, read_content = read_git_object(temp_dir, sha1_hash)

    # Assert that the read type and content match the original
    assert read_type == object_type
    assert read_content == content


# Test for read_git_object function with non-existent object
@pytest.mark.unit
def test_read_git_object_nonexistent(temp_dir: pathlib.Path):
    """
    Test the read_git_object function with a non-existent object.
    """

    # Read a non-existent object
    read_type, read_content = read_git_object(temp_dir, "nonexistentobjecthash")

    # Assert that the read type and content are empty
    assert read_type == ""
    assert read_content == b""


# Test for parse_commit_object function
@pytest.mark.unit
def test_parse_commit_object():
    """
    Test the parse_commit_object function.
    """

    # Create a test commit content
    commit_content = (
        b"tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904\n"
        b"parent 8e4f2a85b4f01bd1e233e50237be2f9c2a6a5a6e\n"
        b"author Test User <test@example.com> 1617235200 +0000\n"
        b"committer Test User <test@example.com> 1617235200 +0000\n"
        b"\n"
        b"Test commit message\n"
    )

    # Parse the commit object
    commit_info = parse_commit_object(commit_content)

    # Assert that the parsed information is correct
    assert commit_info["tree"] == "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    assert commit_info["parent"] == "8e4f2a85b4f01bd1e233e50237be2f9c2a6a5a6e"
    assert commit_info["author"] == "Test User <test@example.com> 1617235200 +0000"
    assert commit_info["committer"] == "Test User <test@example.com> 1617235200 +0000"
    assert commit_info["message"] == "Test commit message"


# Test for parse_commit_object function with minimal content
@pytest.mark.unit
def test_parse_commit_object_minimal():
    """
    Test the parse_commit_object function with minimal content.
    """

    # Create a minimal commit content
    commit_content = b"tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904\n"

    # Parse the commit object
    commit_info = parse_commit_object(commit_content)

    # Assert that the parsed information is correct
    assert commit_info["tree"] == "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    assert commit_info["parent"] is None
    assert commit_info["author"] == ""
    assert commit_info["committer"] == ""
    assert commit_info["message"] == ""


# Test for format_timestamp function
@pytest.mark.unit
def test_format_timestamp():
    """
    Test the format_timestamp function.
    """

    # Create a test timestamp string
    timestamp_str = "Test User <test@example.com> 1617235200 +0000"

    # Format the timestamp
    formatted_date = format_timestamp(timestamp_str)

    # Assert that the formatted date is correct
    assert "+0000" in formatted_date


# Test for get_commit_logs function
@pytest.mark.unit
def test_get_commit_logs(temp_dir: pathlib.Path):
    """
    Test the get_commit_logs function.
    """

    # Create a test commit
    tree_hash = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    author_name = "Test User"
    author_email = "test@example.com"
    message = "Test commit message"

    # Write a tree object
    tree_content = b"test tree content"
    write_object_file(temp_dir, tree_content, "tree")

    # Create a commit object
    commit_hash = create_commit_object(
        temp_dir, tree_hash, None, author_name, author_email, message
    )

    # Update the main branch reference
    update_ref(temp_dir, "refs/heads/main", commit_hash)

    # Get the commit logs
    commit_logs = get_commit_logs(temp_dir)

    # Assert that the commit logs contain the test commit
    assert len(commit_logs) == 1
    assert commit_logs[0]["hash"] == commit_hash
    assert commit_logs[0]["message"] == message


# Test for get_commit_logs function with no repository
@pytest.mark.unit
def test_get_commit_logs_no_repo():
    """
    Test the get_commit_logs function with no repository.
    """

    # Mock the find_git_repo_path function to return None
    with patch("clony.internals.log.find_git_repo_path", return_value=None):
        # Get the commit logs with the current directory
        commit_logs = get_commit_logs()

        # Assert that the commit logs are empty
        assert len(commit_logs) == 0


# Test for get_commit_logs function with no commits
@pytest.mark.unit
def test_get_commit_logs_no_commits(temp_dir: pathlib.Path):
    """
    Test the get_commit_logs function with no commits.
    """

    # Get the commit logs
    commit_logs = get_commit_logs(temp_dir)

    # Assert that the commit logs are empty
    assert len(commit_logs) == 0


# Test for get_commit_logs function with invalid commit
@pytest.mark.unit
def test_get_commit_logs_invalid_commit(temp_dir: pathlib.Path):
    """
    Test the get_commit_logs function with an invalid commit.
    """

    # Update the main branch reference to an invalid commit
    update_ref(temp_dir, "refs/heads/main", "invalidcommithash")

    # Get the commit logs
    commit_logs = get_commit_logs(temp_dir)

    # Assert that the commit logs are empty
    assert len(commit_logs) == 0


# Test for display_commit_logs function
@pytest.mark.unit
def test_display_commit_logs(temp_dir: pathlib.Path):
    """
    Test the display_commit_logs function.
    """

    # Create a test commit
    tree_hash = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    author_name = "Test User"
    author_email = "test@example.com"
    message = "Test commit message"

    # Write a tree object
    tree_content = b"test tree content"
    write_object_file(temp_dir, tree_content, "tree")

    # Create a commit object
    commit_hash = create_commit_object(
        temp_dir, tree_hash, None, author_name, author_email, message
    )

    # Update the main branch reference
    update_ref(temp_dir, "refs/heads/main", commit_hash)

    # Mock the print function to capture output
    with patch("builtins.print") as mock_print:
        # Display the commit logs
        display_commit_logs(temp_dir)

        # Assert that the print function was called with the expected arguments
        mock_print.assert_any_call(f"commit {commit_hash}")
        mock_print.assert_any_call(f"Author: {author_name} <{author_email}>")

        # We can't easily assert the date due to timezone differences
        mock_print.assert_any_call()  # Empty line
        mock_print.assert_any_call(f"    {message}")
        mock_print.assert_any_call()  # Empty line


# Test for display_commit_logs function with no commits
@pytest.mark.unit
def test_display_commit_logs_no_commits(temp_dir: pathlib.Path):
    """
    Test the display_commit_logs function with no commits.
    """

    # Mock the print function to capture output
    with patch("builtins.print") as mock_print:
        # Display the commit logs
        display_commit_logs(temp_dir)

        # Assert that the print function was not called
        mock_print.assert_not_called()


# Test for display_commit_logs function with no repository
@pytest.mark.unit
def test_display_commit_logs_no_repo():
    """
    Test the display_commit_logs function with no repository.
    """
    # Mock the find_git_repo_path function to return None
    with patch("clony.internals.log.find_git_repo_path", return_value=None):
        # Mock the logger to capture error messages
        with patch("clony.internals.log.logger.error") as mock_error:
            # Display the commit logs
            display_commit_logs()

            # Assert that the error message was logged
            mock_error.assert_called_once_with(
                "Not a git repository. Run 'clony init' to create one."
            )
