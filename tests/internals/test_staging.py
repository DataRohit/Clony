"""
Tests for the Git staging functionality.

This module contains tests for the staging functions.
"""

# Standard library imports
import hashlib
import pathlib
import shutil
import sys
import tempfile
import zlib
from typing import Generator
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from clony.core.repository import Repository
from clony.internals.staging import (
    calculate_sha1_hash,
    clear_staging_area,
    compress_content,
    has_file_changed_since_commit,
    is_file_already_staged,
    stage_file,
    update_index_file,
    write_object_file,
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

    # Yield the temporary directory path
    yield temp_path

    # Clean up the temporary directory
    shutil.rmtree(temp_path)


# Test for calculate_sha1_hash function
@pytest.mark.unit
def test_calculate_sha1_hash():
    """
    Test the calculate_sha1_hash function.
    """

    # Define test content
    test_content = b"test content"

    # Calculate SHA-1 hash
    sha1_hash = calculate_sha1_hash(test_content)

    # Assert that the SHA-1 hash is correct
    assert sha1_hash == hashlib.sha1(test_content).hexdigest()


# Test for compress_content function
@pytest.mark.unit
def test_compress_content():
    """
    Test the compress_content function.
    """

    # Define test content
    test_content = b"test content"

    # Compress the content
    compressed_content = compress_content(test_content)

    # Assert that the compressed content is not the same as the original content
    assert compressed_content != test_content

    # Assert that the compressed content can be decompressed
    assert zlib.decompress(compressed_content) == test_content


# Test for write_object_file function
@pytest.mark.unit
def test_write_object_file(temp_dir: pathlib.Path):
    """
    Test the write_object_file function.
    """

    # Define test object directory
    object_dir = temp_dir / "objects"

    # Define test SHA-1 hash
    sha1_hash = "test_sha1_hash"

    # Define test compressed content
    compressed_content = b"test compressed content"

    # Write the object file
    write_object_file(object_dir, sha1_hash, compressed_content)

    # Assert that the object file was created
    assert (object_dir / sha1_hash[:2] / sha1_hash[2:]).exists()


# Test for update_index_file function
@pytest.mark.unit
def test_update_index_file(temp_dir: pathlib.Path):
    """
    Test the update_index_file function.
    """

    # Define test index file
    index_file = temp_dir / "index"

    # Define test file path
    file_path = "test_file_path"

    # Define test SHA-1 hash
    sha1_hash = "test_sha1_hash"

    # Update the index file
    update_index_file(index_file, file_path, sha1_hash)

    # Assert that the index file was updated
    with open(index_file, "r") as f:
        assert f"{file_path} {sha1_hash}\n" in f.read()


# Test for update_index_file function with existing entries
@pytest.mark.unit
def test_update_index_file_with_existing_entries(temp_dir: pathlib.Path):
    """
    Test the update_index_file function when there are existing entries in the index.
    """

    # Define test index file
    index_file = temp_dir / "index"

    # Create initial index content with multiple entries
    initial_content = "file1.txt abc123\nfile2.txt def456\nfile3.txt ghi789\n"
    index_file.write_text(initial_content)

    # Define test file path and SHA-1 hash
    file_path = "file2.txt"
    sha1_hash = "new_hash_123"

    # Update the index file
    update_index_file(index_file, file_path, sha1_hash)

    # Assert that the index file was updated correctly
    with open(index_file, "r") as f:
        content = f.read()
        # Check that file1.txt entry is unchanged
        assert "file1.txt abc123" in content

        # Check that file2.txt entry is updated
        assert "file2.txt new_hash_123" in content

        # Check that file3.txt entry is unchanged
        assert "file3.txt ghi789" in content


# Test for stage_file function
@pytest.mark.unit
def test_stage_file(temp_dir: pathlib.Path):
    """
    Test the stage_file function.
    """

    # Define test file path
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file content.")

    # Initialize Repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Stage the test file
    # Call stage_file function
    stage_file(str(test_file_path))

    # Calculate SHA-1 hash of the file content
    file_content = test_file_path.read_bytes()
    sha1_hash = hashlib.sha1(file_content).hexdigest()

    # Define object file path
    object_file_path = repo.git_dir / "objects" / sha1_hash[:2] / sha1_hash[2:]

    # Assert object file exists
    assert object_file_path.exists()

    # Define index file path
    index_file_path = repo.git_dir / "index"

    # Assert index file updated
    assert index_file_path.exists()
    with open(index_file_path, "r") as index_file:
        # Read index file content
        index_content = index_file.read()

        # Assert test file path in index content
        assert str(test_file_path) in index_content

        # Assert SHA-1 hash in index content
        assert sha1_hash in index_content


# Test for stage_file function when no git repo is found
@pytest.mark.unit
def test_stage_file_no_repo_found(temp_dir: pathlib.Path):
    """
    Test the stage_file function when no Git repository is found.
    """

    # Define test file path outside git repo
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file content.")

    # Mock the logger.debug and logger.error functions
    with patch("clony.internals.staging.logger.error") as mock_logger_error:
        # Stage the test file which is not in a git repo
        result = stage_file(str(test_file_path))

        # Verify that the function returned None
        assert result is None

        # Verify that logger.error was called with the correct message
        mock_logger_error.assert_called_with(
            "Not a git repository. Run 'clony init' to create one."
        )


# Test for stage_file function with exception during file reading
@pytest.mark.unit
def test_stage_file_exception_reading_file(temp_dir: pathlib.Path):
    """
    Test the stage_file function when an exception occurs during file reading.
    """

    # Define test file path
    test_file_path = temp_dir / "test_file.txt"

    # Initialize Repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Stage the test file but simulate an error during file reading
    with patch("builtins.open", side_effect=IOError("Mocked IOError")):
        with patch("clony.internals.staging.logger.error") as mock_logger_error:
            with pytest.raises(SystemExit):
                stage_file(str(test_file_path))

            # Verify that logger.error was called with the correct message
            mock_logger_error.assert_called_with("Error staging file: Mocked IOError")


# Test for stage_file function with generic exception
@pytest.mark.unit
def test_stage_file_generic_exception(temp_dir: pathlib.Path):
    """
    Test the stage_file function when a generic exception occurs.
    """

    # Define test file path
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file content.")

    # Initialize Repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Mock write_object_file to raise a generic exception
    with patch(
        "clony.internals.staging.write_object_file",
        side_effect=Exception("Generic Mocked Exception"),
    ):
        with patch("clony.internals.staging.logger.error") as mock_logger_error:
            with pytest.raises(SystemExit):
                stage_file(str(test_file_path))

            # Verify that logger.error was called with the correct message
            mock_logger_error.assert_called_with(
                "Error staging file: Generic Mocked Exception"
            )


# Test for stage_file function when file is already staged
@pytest.mark.unit
def test_stage_file_already_staged(temp_dir: pathlib.Path):
    """
    Test the stage_file function when the file is already staged.
    """

    # Define test file path
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file content.")

    # Initialize Repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Stage the file first time - this should succeed
    stage_file(str(test_file_path))

    # Try to stage the same file again - this should log a warning
    with patch("clony.internals.staging.logger.warning") as mock_logger_warning:
        stage_file(str(test_file_path))

        # Verify that logger.warning was called with the correct message
        mock_logger_warning.assert_called_with(
            f"File already staged: '{str(test_file_path)}'"
        )


# Test for is_file_already_staged function
@pytest.mark.unit
def test_is_file_already_staged(temp_dir: pathlib.Path):
    """
    Test the is_file_already_staged function.
    """

    # Create a test index file
    index_file = temp_dir / "index"

    # Test when index file doesn't exist
    assert not is_file_already_staged(index_file, "test_file.txt", "hash123")

    # Create the index file with a test entry
    with open(index_file, "w") as f:
        f.write("test_file.txt hash123\n")
        f.write("other_file.txt hash456\n")

    # Test when file is in index with matching hash
    assert is_file_already_staged(index_file, "test_file.txt", "hash123")

    # Test when file is in index with different hash
    assert not is_file_already_staged(index_file, "test_file.txt", "different_hash")

    # Test when file is not in index
    assert not is_file_already_staged(index_file, "non_existent_file.txt", "hash789")


# Test for clear_staging_area function
@pytest.mark.unit
def test_clear_staging_area(temp_dir: pathlib.Path):
    """
    Test the clear_staging_area function.
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

    # Clear the staging area
    clear_staging_area(temp_dir)

    # Verify that the index file exists but is empty
    assert index_file.exists()
    with open(index_file, "r") as f:
        content = f.read()
    assert content.strip() == ""


# Test for has_file_changed_since_commit function
@pytest.mark.unit
def test_has_file_changed_since_commit(temp_dir: pathlib.Path):
    """
    Test the has_file_changed_since_commit function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_content = "test content"
    test_file_path.write_text(test_file_content)

    # Calculate the SHA-1 hash of the content
    content_hash = calculate_sha1_hash(test_file_content.encode())

    # Check if the file has changed
    # (it should have, as it's not in the objects directory yet)
    assert has_file_changed_since_commit(temp_dir, str(test_file_path), content_hash)

    # Stage the file to create the object
    with patch.object(sys, "argv", ["clony", "stage", str(test_file_path)]):
        stage_file(str(test_file_path))

    # Create a file outside the repository
    outside_file_path = pathlib.Path(tempfile.gettempdir()) / "outside_file.txt"
    outside_file_path.write_text("outside content")

    # Check if the outside file has changed
    # (it should have, as it's outside the repository)
    assert has_file_changed_since_commit(
        temp_dir,
        str(outside_file_path),
        calculate_sha1_hash("outside content".encode()),
    )

    # Test with an exception
    with patch("pathlib.Path.relative_to", side_effect=Exception("Test exception")):
        assert has_file_changed_since_commit(
            temp_dir, str(test_file_path), content_hash
        )


# Test for has_file_changed_since_commit function with non-existent object
@pytest.mark.unit
def test_has_file_changed_since_commit_non_existent_object(temp_dir: pathlib.Path):
    """
    Test the has_file_changed_since_commit function when the object doesn't exist.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_content = "test content"
    test_file_path.write_text(test_file_content)

    # Calculate the SHA-1 hash of the content
    content_hash = calculate_sha1_hash(test_file_content.encode())

    # Create the object directory structure but not the object file itself
    objects_dir = temp_dir / ".git" / "objects"
    object_subdir = objects_dir / content_hash[:2]
    object_subdir.mkdir(parents=True, exist_ok=True)

    # The object file doesn't exist, so has_file_changed_since_commit should return True
    assert has_file_changed_since_commit(temp_dir, str(test_file_path), content_hash)


# Test for has_file_changed_since_commit function with unchanged file
@pytest.mark.unit
def test_has_file_changed_since_commit_unchanged_file(temp_dir: pathlib.Path):
    """
    Test the has_file_changed_since_commit function when the file hasn't changed.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_content = "test content"
    test_file_path.write_text(test_file_content)

    # Calculate the SHA-1 hash of the content
    content_hash = calculate_sha1_hash(test_file_content.encode())

    # Stage the file to create the object
    with patch.object(sys, "argv", ["clony", "stage", str(test_file_path)]):
        stage_file(str(test_file_path))

    # Create the object file manually to ensure it exists
    objects_dir = temp_dir / ".git" / "objects"
    object_subdir = objects_dir / content_hash[:2]
    object_file = object_subdir / content_hash[2:]

    # Ensure the object file exists
    assert object_file.exists()

    # The file hasn't changed, so has_file_changed_since_commit should return False
    assert not has_file_changed_since_commit(
        temp_dir, str(test_file_path), content_hash
    )


# Test for stage_file function when file hasn't changed since last commit
@pytest.mark.unit
def test_stage_file_unchanged_since_commit(temp_dir: pathlib.Path):
    """
    Test the stage_file function when the file hasn't changed since the last commit.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_content = "test content"
    test_file_path.write_text(test_file_content)

    # Stage the file first time - this should succeed
    stage_file(str(test_file_path))

    # Create a commit to record the file state
    with patch("clony.internals.commit.find_git_repo_path", return_value=temp_dir):
        # Call the make_commit function
        from clony.internals.commit import make_commit

        # Call the make_commit function
        make_commit("Initial commit", "Test Author", "test@example.com")

    # Mock the logger.warning function
    with patch("clony.internals.staging.logger.warning") as mock_logger_warning:
        # Stage the file again - this should warn about unchanged file
        stage_file(str(test_file_path))

        # Verify that logger.warning was called with the correct message
        mock_logger_warning.assert_called_with(
            f"File unchanged since last commit: '{str(test_file_path)}'"
        )

    # Verify that the index file is empty
    index_file = temp_dir / ".git" / "index"
    assert index_file.exists()
    with open(index_file, "r") as f:
        content = f.read()
    assert content.strip() == ""


# Test for has_file_changed_since_commit function with missing object file
@pytest.mark.unit
def test_has_file_changed_since_commit_missing_object_file(temp_dir: pathlib.Path):
    """
    Test the has_file_changed_since_commit function when the object file should exist
    but doesn't. This tests the specific case where the file is in the staging area
    but the object file is missing.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_content = "test content"
    test_file_path.write_text(test_file_content)

    # Calculate the SHA-1 hash of the content
    content_hash = calculate_sha1_hash(test_file_content.encode())

    # Create the index file with the test file entry
    index_file = temp_dir / ".git" / "index"
    with open(index_file, "w") as f:
        f.write(f"{str(test_file_path)} {content_hash}\n")

    # Create the objects directory structure but not the object file itself
    objects_dir = temp_dir / ".git" / "objects"
    object_subdir = objects_dir / content_hash[:2]
    object_subdir.mkdir(parents=True, exist_ok=True)

    # The object file doesn't exist, so has_file_changed_since_commit should return True
    assert has_file_changed_since_commit(temp_dir, str(test_file_path), content_hash)


# Test for stage_file function when file hasn't changed but is not in staging area
@pytest.mark.unit
def test_stage_file_unchanged_not_staged(temp_dir: pathlib.Path):
    """
    Test the stage_file function when the file hasn't changed since the last commit
    but is not in the staging area. This tests the specific warning case.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_content = "test content"
    test_file_path.write_text(test_file_content)

    # Calculate the SHA-1 hash of the content
    content_hash = calculate_sha1_hash(test_file_content.encode())

    # Create the object file manually to simulate a previous commit
    objects_dir = temp_dir / ".git" / "objects"
    object_subdir = objects_dir / content_hash[:2]
    object_subdir.mkdir(parents=True, exist_ok=True)
    object_file = object_subdir / content_hash[2:]

    # Write some content to the object file
    with open(object_file, "wb") as f:
        f.write(compress_content(test_file_content.encode()))

    # Mock has_file_changed_since_commit to return False
    with patch(
        "clony.internals.staging.has_file_changed_since_commit", return_value=False
    ):
        with patch("clony.internals.staging.logger.warning") as mock_logger_warning:
            # Try to stage the file
            stage_file(str(test_file_path))

            # Verify that logger.warning was called with the correct message
            mock_logger_warning.assert_called_with(
                f"File unchanged since last commit: '{str(test_file_path)}'"
            )


# Test for stage_file function when file hasn't changed after a commit
# with content modification
@pytest.mark.unit
def test_stage_file_unchanged_after_commit_with_modification(temp_dir: pathlib.Path):
    """
    Test that a file cannot be staged after a commit if it hasn't changed,
    even after the file was modified before the commit.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("initial content")

    # Stage the file first time
    stage_file(str(test_file_path))

    # Modify the file and stage it again
    test_file_path.write_text("modified content")
    stage_file(str(test_file_path))

    # Create a commit
    with patch("clony.internals.commit.find_git_repo_path", return_value=temp_dir):
        from clony.internals.commit import make_commit

        make_commit("Initial commit", "Test Author", "test@example.com")

    # Try to stage the same file again without changes
    with patch("clony.internals.staging.logger.warning") as mock_logger_warning:
        stage_file(str(test_file_path))

        # Verify that logger.warning was called with the correct message
        mock_logger_warning.assert_called_with(
            f"File unchanged since last commit: '{str(test_file_path)}'"
        )

    # Verify that the index file is empty
    index_file = temp_dir / ".git" / "index"
    assert index_file.exists()
    with open(index_file, "r") as f:
        content = f.read()
    assert content.strip() == ""


# Test for display_staging_info function
@pytest.mark.unit
def test_display_staging_info():
    """
    Test the display_staging_info function.

    This test verifies that the display_staging_info function correctly creates
    and displays a table with staging information including file path, status,
    and content hash.
    """
    # Define test parameters
    file_path = "test_file.txt"
    file_hash = "0123456789abcdef0123456789abcdef01234567"
    status = "STAGED"

    # Mock the console.print method
    with patch("clony.internals.staging.console.print") as mock_console_print:
        # Call the display_staging_info function
        from clony.internals.staging import display_staging_info

        display_staging_info(file_path, file_hash, status)

        # Verify that console.print was called once
        assert mock_console_print.call_count == 1

        # Verify that the argument to console.print is a Table
        from rich.table import Table

        assert isinstance(mock_console_print.call_args[0][0], Table)

        # Get the table that was passed to console.print
        table = mock_console_print.call_args[0][0]

        # Verify the table title
        assert table.title == "Staging Results"

        # Verify the table has the expected columns
        column_names = [column.header for column in table.columns]
        assert "File Path" in column_names
        assert "Status" in column_names
        assert "Content Hash" in column_names
