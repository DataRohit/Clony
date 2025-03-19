"""
Tests for the Git commit functionality.

This module contains tests for the commit functions.
"""

# Standard library imports
import pathlib
import shutil
import sys
import tempfile
from typing import Generator
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from clony.core.refs import get_head_commit, get_ref_hash
from clony.core.repository import Repository
from clony.internals.commit import display_commit_info, make_commit, read_index_file
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


# Test for read_index_file function
@pytest.mark.unit
def test_read_index_file(temp_dir: pathlib.Path):
    """
    Test the read_index_file function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create an index file with test content
    index_file = temp_dir / ".git" / "index"
    index_content = "file1.txt 1234567890abcdef1234567890abcdef12345678\n"
    index_content += "file2.txt 9876543210abcdef1234567890abcdef12345678\n"
    with open(index_file, "w") as f:
        f.write(index_content)

    # Read the index file
    index_dict = read_index_file(index_file)

    # Assert that the index dictionary contains the expected entries
    assert len(index_dict) == 2
    assert index_dict["file1.txt"] == "1234567890abcdef1234567890abcdef12345678"
    assert index_dict["file2.txt"] == "9876543210abcdef1234567890abcdef12345678"

    # Test with a non-existent index file
    non_existent_index = temp_dir / "non_existent_index"
    index_dict = read_index_file(non_existent_index)

    # Assert that the index dictionary is empty
    assert len(index_dict) == 0


# Test for commit function
@pytest.mark.unit
def test_commit(temp_dir: pathlib.Path):
    """
    Test the commit function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("test content")

    # Stage the test file
    with patch.object(sys, "argv", ["clony", "stage", str(test_file_path)]):
        stage_file(str(test_file_path))

    # Define commit parameters
    message = "Test commit message"
    author_name = "Test Author"
    author_email = "test@example.com"

    # Create a commit
    with patch("clony.internals.commit.find_git_repo_path", return_value=temp_dir):
        commit_hash = make_commit(message, author_name, author_email)

    # Assert that the commit hash is not None
    assert commit_hash is not None

    # Assert that the HEAD commit is the new commit
    head_commit = get_head_commit(temp_dir)
    assert head_commit == commit_hash

    # Assert that the main branch points to the new commit
    main_commit = get_ref_hash(temp_dir, "refs/heads/main")
    assert main_commit == commit_hash


# Test for commit function with no staged changes
@pytest.mark.unit
def test_commit_no_staged_changes(temp_dir: pathlib.Path):
    """
    Test the commit function when there are no staged changes.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Define commit parameters
    message = "Test commit message"
    author_name = "Test Author"
    author_email = "test@example.com"

    # Try to create a commit with no staged changes
    with patch("clony.internals.commit.find_git_repo_path", return_value=temp_dir):
        with patch("clony.internals.commit.logger.error") as mock_logger_error:
            with pytest.raises(SystemExit):
                make_commit(message, author_name, author_email)

            # Verify that logger.error was called with the correct message
            mock_logger_error.assert_called_with(
                "Nothing to commit. Run 'clony stage <file>' to stage changes."
            )


# Test for commit function when no git repo is found
@pytest.mark.unit
def test_commit_no_repo_found(temp_dir: pathlib.Path):
    """
    Test the commit function when no Git repository is found.
    """

    # Define commit parameters
    message = "Test commit message"
    author_name = "Test Author"
    author_email = "test@example.com"

    # Try to create a commit with no git repo
    with patch("clony.internals.commit.find_git_repo_path", return_value=None):
        with patch("clony.internals.commit.logger.error") as mock_logger_error:
            with pytest.raises(SystemExit):
                make_commit(message, author_name, author_email)

            # Verify that logger.error was called with the correct message
            mock_logger_error.assert_called_with(
                "Not a git repository. Run 'clony init' to create one."
            )


# Test for commit function with generic exception
@pytest.mark.unit
def test_commit_generic_exception(temp_dir: pathlib.Path):
    """
    Test the commit function when a generic exception occurs.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("test content")

    # Stage the test file
    with patch.object(sys, "argv", ["clony", "stage", str(test_file_path)]):
        stage_file(str(test_file_path))

    # Define commit parameters
    message = "Test commit message"
    author_name = "Test Author"
    author_email = "test@example.com"

    # Try to create a commit with a generic exception
    with patch("clony.internals.commit.find_git_repo_path", return_value=temp_dir):
        with patch(
            "clony.internals.commit.create_tree_object",
            side_effect=Exception("Generic Mocked Exception"),
        ):
            with patch("clony.internals.commit.logger.error") as mock_logger_error:
                with pytest.raises(SystemExit):
                    make_commit(message, author_name, author_email)

                # Verify that logger.error was called with the correct message
                mock_logger_error.assert_called_with(
                    "Error creating commit: Generic Mocked Exception"
                )


# Test for commit function with detached HEAD
@pytest.mark.unit
def test_commit_detached_head(temp_dir: pathlib.Path):
    """
    Test the commit function when HEAD is detached.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("test content")

    # Stage the test file
    with patch.object(sys, "argv", ["clony", "stage", str(test_file_path)]):
        stage_file(str(test_file_path))

    # Set HEAD to a detached state (direct commit hash)
    detached_commit_hash = "1234567890abcdef1234567890abcdef12345678"
    with open(temp_dir / ".git" / "HEAD", "w") as f:
        f.write(detached_commit_hash)

    # Define commit parameters
    message = "Test commit message"
    author_name = "Test Author"
    author_email = "test@example.com"

    # Create a commit with detached HEAD
    with patch("clony.internals.commit.find_git_repo_path", return_value=temp_dir):
        commit_hash = make_commit(message, author_name, author_email)

    # Assert that the commit hash is not None
    assert commit_hash is not None

    # Assert that HEAD is updated to the new commit
    with open(temp_dir / ".git" / "HEAD", "r") as f:
        head_content = f.read().strip()
        assert head_content == commit_hash


# Test for commit function with empty index file
@pytest.mark.unit
def test_commit_empty_index_file(temp_dir: pathlib.Path):
    """
    Test the commit function when the index file exists but is empty.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create an empty index file
    index_file = temp_dir / ".git" / "index"
    index_file.touch()  # Create an empty file

    # Define commit parameters
    message = "Test commit message"
    author_name = "Test Author"
    author_email = "test@example.com"

    # Try to create a commit with an empty index file
    with patch("clony.internals.commit.find_git_repo_path", return_value=temp_dir):
        with patch("clony.internals.commit.logger.error") as mock_logger_error:
            with pytest.raises(SystemExit):
                make_commit(message, author_name, author_email)

            # Verify that logger.error was called with the correct message
            mock_logger_error.assert_called_with(
                "Nothing to commit. Run 'clony stage <file>' to stage changes."
            )


# Test for commit function clearing staging area
@pytest.mark.unit
def test_commit_clears_staging_area(temp_dir: pathlib.Path):
    """
    Test that the commit function clears the staging area after a successful commit.
    """
    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("test content")

    # Stage the test file
    with patch.object(sys, "argv", ["clony", "stage", str(test_file_path)]):
        stage_file(str(test_file_path))

    # Define the index file path
    index_file = temp_dir / ".git" / "index"

    # Verify that the index file exists and has content
    assert index_file.exists()
    with open(index_file, "r") as f:
        content = f.read()
    assert content.strip() != ""

    # Define commit parameters
    message = "Test commit message"
    author_name = "Test Author"
    author_email = "test@example.com"

    # Create a commit
    with patch("clony.internals.commit.find_git_repo_path", return_value=temp_dir):
        make_commit(message, author_name, author_email)

    # Verify that the index file exists but is empty (staging area cleared)
    assert index_file.exists()
    with open(index_file, "r") as f:
        content = f.read()
    assert content.strip() == ""


# Test for make_commit function updating HEAD_TREE file
@pytest.mark.unit
def test_make_commit_updates_head_tree(tmp_path):
    """Test that make_commit updates the HEAD_TREE file."""

    # Create a test repository
    repo_path = tmp_path / "repo"
    repo_path.mkdir()

    # Mock the necessary functions
    with (
        patch("clony.internals.commit.find_git_repo_path", return_value=repo_path),
        patch(
            "clony.internals.commit.read_index_file",
            side_effect=[
                {"test.txt": "hash1"},
                {"existing.txt": "hash2"},
            ],
        ),
        patch("clony.internals.commit.create_tree_object", return_value="tree_hash"),
        patch("clony.internals.commit.get_head_commit", return_value="parent_hash"),
        patch(
            "clony.internals.commit.create_commit_object", return_value="commit_hash"
        ),
        patch("clony.internals.commit.get_head_ref", return_value="refs/heads/main"),
        patch("clony.internals.commit.update_ref"),
        patch("clony.internals.commit.clear_staging_area"),
    ):

        # Create the .git directory
        git_dir = repo_path / ".git"
        git_dir.mkdir()

        # Create the index file
        index_file = git_dir / "index"
        index_file.touch()

        # Create the HEAD_TREE file with existing content
        head_tree_file = git_dir / "HEAD_TREE"
        with open(head_tree_file, "w") as f:
            f.write("existing.txt hash2\n")

        # Call make_commit
        make_commit("Test commit", "Test Author", "test@example.com")

        # Check that the HEAD_TREE file was updated
        with open(head_tree_file, "r") as f:
            content = f.read()

        # Verify that both the existing and new files are in the HEAD_TREE file
        assert "test.txt hash1" in content
        assert "existing.txt hash2" in content


@pytest.mark.unit
def test_display_commit_info_error():
    """
    Test that display_commit_info handles errors correctly.
    """
    # Mock the console.print to raise an exception
    with patch(
        "clony.internals.commit.console.print", side_effect=Exception("Test error")
    ):
        # Mock the logger.error function to track calls
        with patch("clony.internals.commit.logger.error") as mock_logger:
            # Call the display_commit_info function
            display_commit_info("commit_hash", "message", "author_name", "author_email")

            # Verify that logger.error was called with the correct error message
            mock_logger.assert_called_once_with(
                "Error displaying commit information: Test error"
            )
