"""
Tests for the Git objects functionality.

This module contains tests for the objects module, including blob, tree,
and commit objects.
"""

# Standard library imports
import hashlib
import os
import pathlib
import shutil
import stat
import tempfile
import zlib
from typing import Generator
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from clony.core.objects import (
    calculate_sha1_hash,
    compress_content,
    create_blob_object,
    create_commit_object,
    create_tree_object,
    write_object_file,
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


# Test for calculate_sha1_hash function
@pytest.mark.unit
def test_calculate_sha1_hash():
    """
    Test the calculate_sha1_hash function.
    """

    # Define test content
    content = b"test content"

    # Calculate SHA-1 hash using the function
    sha1_hash = calculate_sha1_hash(content)

    # Calculate expected SHA-1 hash
    expected_hash = hashlib.sha1(content).hexdigest()

    # Assert that the calculated hash matches the expected hash
    assert sha1_hash == expected_hash


# Test for compress_content function
@pytest.mark.unit
def test_compress_content():
    """
    Test the compress_content function.
    """

    # Define test content
    content = b"test content"

    # Compress the content using the function
    compressed_content = compress_content(content)

    # Compress the content using zlib directly
    expected_compressed = zlib.compress(content)

    # Assert that the compressed content matches the expected compressed content
    assert compressed_content == expected_compressed


# Test for write_object_file function
@pytest.mark.unit
def test_write_object_file(temp_dir: pathlib.Path):
    """
    Test the write_object_file function.
    """

    # Define test content
    content = b"test content"
    object_type = "blob"

    # Write the object file
    sha1_hash = write_object_file(temp_dir, content, object_type)

    # Calculate expected SHA-1 hash
    header = f"{object_type} {len(content)}\0".encode()
    store_content = header + content
    expected_hash = hashlib.sha1(store_content).hexdigest()

    # Assert that the returned hash matches the expected hash
    assert sha1_hash == expected_hash

    # Assert that the object file was created
    object_file_path = temp_dir / ".git" / "objects" / sha1_hash[:2] / sha1_hash[2:]
    assert object_file_path.exists()

    # Read the object file and decompress it
    with open(object_file_path, "rb") as f:
        compressed_content = f.read()
    decompressed_content = zlib.decompress(compressed_content)

    # Assert that the decompressed content matches the original content with header
    assert decompressed_content == store_content


# Test for create_blob_object function
@pytest.mark.unit
def test_create_blob_object(temp_dir: pathlib.Path):
    """
    Test the create_blob_object function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_content = "test content"
    test_file_path.write_text(test_content)

    # Create a blob object
    _ = create_blob_object(temp_dir, test_file_path)

    # Calculate expected SHA-1 hash
    header = f"blob {len(test_content.encode())}\0".encode()
    store_content = header + test_content.encode()
    expected_hash = hashlib.sha1(store_content).hexdigest()

    # Assert that the returned hash matches the expected hash
    assert expected_hash

    # Assert that the object file was created
    object_file_path = (
        temp_dir / ".git" / "objects" / expected_hash[:2] / expected_hash[2:]
    )
    assert object_file_path.exists()


# Test for create_tree_object function
@pytest.mark.unit
def test_create_tree_object(temp_dir: pathlib.Path):
    """
    Test the create_tree_object function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test directory structure
    test_dir = temp_dir / "test_dir"
    test_dir.mkdir()
    test_file1 = test_dir / "file1.txt"
    test_file1.write_text("file1 content")
    test_file2 = test_dir / "file2.txt"
    test_file2.write_text("file2 content")

    test_subdir = test_dir / "subdir"
    test_subdir.mkdir()
    test_file3 = test_subdir / "file3.txt"
    test_file3.write_text("file3 content")

    # Create a tree object
    sha1_hash = create_tree_object(temp_dir, test_dir)

    # Assert that the object file was created
    object_file_path = temp_dir / ".git" / "objects" / sha1_hash[:2] / sha1_hash[2:]
    assert object_file_path.exists()

    # Assert that blob objects were created for the files
    for file_path in [test_file1, test_file2, test_file3]:
        # Read the file content
        content = file_path.read_bytes()

        # Calculate the SHA-1 hash
        header = f"blob {len(content)}\0".encode()
        store_content = header + content
        file_hash = hashlib.sha1(store_content).hexdigest()

        # Assert that the object file was created
        file_object_path = temp_dir / ".git" / "objects" / file_hash[:2] / file_hash[2:]
        assert file_object_path.exists()


# Test for create_tree_object function with executable file
@pytest.mark.unit
def test_create_tree_object_with_executable(temp_dir: pathlib.Path):
    """
    Test the create_tree_object function with an executable file.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test directory
    test_dir = temp_dir / "test_dir_exec"
    test_dir.mkdir()

    # Create a regular file
    test_file = test_dir / "file.txt"
    test_file.write_text("regular file content")

    # Create a file that will be treated as executable
    test_exec = test_dir / "script.sh"
    test_exec.write_text("#!/bin/bash\necho 'Hello, World!'")

    # Mock the stat function to make the file appear executable
    original_stat = os.stat

    def mock_stat(path, *args, **kwargs):
        result = original_stat(path, *args, **kwargs)
        if str(path).endswith("script.sh"):
            # Create a new stat result with executable bit set
            # This is a bit hacky but works for testing
            mode = result.st_mode | stat.S_IXUSR

            # Create a new object with the modified mode
            class MockStatResult:
                def __init__(self, original, new_mode):
                    self.st_mode = new_mode
                    # Copy all other attributes
                    for attr in dir(original):
                        if not attr.startswith("__") and attr != "st_mode":
                            setattr(self, attr, getattr(original, attr))

            return MockStatResult(result, mode)
        return result

    # Apply the mock
    with patch("os.stat", side_effect=mock_stat):
        # Create a tree object
        sha1_hash = create_tree_object(temp_dir, test_dir)

        # Assert that the object file was created
        object_file_path = temp_dir / ".git" / "objects" / sha1_hash[:2] / sha1_hash[2:]
        assert object_file_path.exists()

        # Assert that blob objects were created for the files
        for file_path in [test_file, test_exec]:
            content = file_path.read_bytes()
            header = f"blob {len(content)}\0".encode()
            store_content = header + content
            file_hash = hashlib.sha1(store_content).hexdigest()
            file_object_path = (
                temp_dir / ".git" / "objects" / file_hash[:2] / file_hash[2:]
            )
            assert file_object_path.exists()


# Test for create_commit_object function
@pytest.mark.unit
def test_create_commit_object(temp_dir: pathlib.Path):
    """
    Test the create_commit_object function.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("test content")

    # Create a blob object for the test file
    _ = create_blob_object(temp_dir, test_file_path)

    # Create a tree object
    tree_hash = create_tree_object(temp_dir, temp_dir)

    # Define commit parameters
    parent_hash = None
    author_name = "Test Author"
    author_email = "test@example.com"
    message = "Test commit message"

    # Create a commit object
    commit_hash = create_commit_object(
        temp_dir, tree_hash, parent_hash, author_name, author_email, message
    )

    # Assert that the object file was created
    object_file_path = temp_dir / ".git" / "objects" / commit_hash[:2] / commit_hash[2:]
    assert object_file_path.exists()

    # Read the commit object and verify its content
    with open(object_file_path, "rb") as f:
        compressed_content = f.read()
    decompressed_content = zlib.decompress(compressed_content)

    # Verify that the commit content contains the expected information
    commit_content = decompressed_content.decode()
    assert f"tree {tree_hash}" in commit_content
    assert f"author {author_name} <{author_email}>" in commit_content
    assert f"committer {author_name} <{author_email}>" in commit_content
    assert message in commit_content


# Test for create_commit_object function with parent commit
@pytest.mark.unit
def test_create_commit_object_with_parent(temp_dir: pathlib.Path):
    """
    Test the create_commit_object function with a parent commit.
    """

    # Initialize a repository
    repo = Repository(str(temp_dir))
    repo.init()

    # Create a test file
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("test content")

    # Create a blob object for the test file
    _ = create_blob_object(temp_dir, test_file_path)

    # Create a tree object
    tree_hash = create_tree_object(temp_dir, temp_dir)

    # Define first commit parameters
    parent_hash = None
    author_name = "Test Author"
    author_email = "test@example.com"
    message = "First commit message"

    # Create the first commit object
    first_commit_hash = create_commit_object(
        temp_dir, tree_hash, parent_hash, author_name, author_email, message
    )

    # Modify the test file
    test_file_path.write_text("updated test content")

    # Create a new blob object for the updated file
    _ = create_blob_object(temp_dir, test_file_path)

    # Create a new tree object
    updated_tree_hash = create_tree_object(temp_dir, temp_dir)

    # Define second commit parameters with parent
    second_message = "Second commit message"

    # Create the second commit object with parent
    second_commit_hash = create_commit_object(
        temp_dir,
        updated_tree_hash,
        first_commit_hash,
        author_name,
        author_email,
        second_message,
    )

    # Assert that the object file was created
    object_file_path = (
        temp_dir / ".git" / "objects" / second_commit_hash[:2] / second_commit_hash[2:]
    )
    assert object_file_path.exists()

    # Read the commit object and verify its content
    with open(object_file_path, "rb") as f:
        compressed_content = f.read()

    # Decompress the content
    decompressed_content = zlib.decompress(compressed_content)

    # Verify that the commit content contains the expected information
    commit_content = decompressed_content.decode()
    assert f"tree {updated_tree_hash}" in commit_content
    assert f"parent {first_commit_hash}" in commit_content
    assert f"author {author_name} <{author_email}>" in commit_content
    assert f"committer {author_name} <{author_email}>" in commit_content
    assert second_message in commit_content
