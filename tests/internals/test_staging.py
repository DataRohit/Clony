"""
Tests for the Git staging functionality.

This module contains tests for the staging functions.
"""

# Standard library imports
import hashlib
import pathlib
import shutil
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
    compress_content,
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
