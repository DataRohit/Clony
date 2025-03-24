"""
Tests for the merge functionality.

This module contains tests for the merge functions.
"""

# Standard library imports
import hashlib
import os
import pathlib
import shutil
import tempfile
import time
import zlib
from typing import Generator, List, Tuple
from unittest import mock
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from clony.internals.merge import (
    detect_conflicts,
    display_merge_results,
    get_files_in_tree,
    identify_changes,
    is_binary_content,
    perform_merge,
    three_way_merge,
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


# Helper function to create Git objects
def create_git_object(repo_path: pathlib.Path, content: bytes, obj_type: str) -> str:
    """
    Create a Git object in the repository.

    Args:
        repo_path (pathlib.Path): Path to the repository.
        content (bytes): Content of the object.
        obj_type (str): Type of the object (blob, tree, commit).

    Returns:
        str: SHA-1 hash of the object.
    """

    # Create the object header
    header = f"{obj_type} {len(content)}\0".encode()

    # Combine the header and content
    store_content = header + content

    # Calculate the SHA-1 hash
    sha1_hash = hashlib.sha1(store_content).hexdigest()

    # Define the object path
    objects_dir = repo_path / ".git" / "objects"
    objects_dir.mkdir(parents=True, exist_ok=True)

    # Create the object directory
    obj_dir = objects_dir / sha1_hash[:2]
    obj_dir.mkdir(exist_ok=True)

    # Define the object file path
    obj_file = obj_dir / sha1_hash[2:]

    # Write the compressed content to the file
    with open(obj_file, "wb") as f:
        f.write(zlib.compress(store_content))

    # Return the hash
    return sha1_hash


# Helper function to create a commit object
def create_commit_object(
    repo_path: pathlib.Path,
    tree_hash: str,
    parent_hash: str = None,
    message: str = "Test commit",
    author: str = "Test Author <test@example.com>",
) -> str:
    """
    Create a commit object in the repository.

    Args:
        repo_path (pathlib.Path): Path to the repository.
        tree_hash (str): Hash of the tree object.
        parent_hash (str, optional): Hash of the parent commit. Defaults to None.
        message (str, optional): Commit message. Defaults to "Test commit".
        author (str, optional): Author information.
            Defaults to "Test Author <test@example.com>".

    Returns:
        str: SHA-1 hash of the commit object.
    """

    # Create the commit content
    content = f"tree {tree_hash}\n"
    if parent_hash:
        content += f"parent {parent_hash}\n"

    # Get the current timestamp
    timestamp = int(time.time())

    # Get the timezone offset
    timezone = "-0500"

    # Add the author and committer lines
    content += f"author {author} {timestamp} {timezone}\n"
    content += f"committer {author} {timestamp} {timezone}\n"
    content += f"\n{message}\n"

    # Create the commit object
    return create_git_object(repo_path, content.encode(), "commit")


# Helper function to create a tree object with entries
def create_tree_object(
    repo_path: pathlib.Path, entries: List[Tuple[str, str, str, str]]
) -> str:
    """
    Create a tree object in the repository.

    Args:
        repo_path (pathlib.Path): Path to the repository.
        entries (List[Tuple[str, str, str, str]]): List of entries
            (mode, type, name, hash).

    Returns:
        str: SHA-1 hash of the tree object.
    """

    # Initialize the tree content
    content = b""

    # Add each entry to the tree content
    for mode, obj_type, name, obj_hash in entries:
        # Convert the hash from hex to binary
        hash_bin = bytes.fromhex(obj_hash)

        # Create the entry
        entry = f"{mode} {name}\0".encode() + hash_bin
        content += entry

    # Create the tree object
    return create_git_object(repo_path, content, "tree")


# Helper function to create a blob object
def create_blob_object(repo_path: pathlib.Path, content: bytes) -> str:
    """
    Create a blob object in the repository.

    Args:
        repo_path (pathlib.Path): Path to the repository.
        content (bytes): Content of the blob.

    Returns:
        str: SHA-1 hash of the blob object.
    """

    # Create the blob object
    return create_git_object(repo_path, content, "blob")


# Test for identify_changes function
@pytest.mark.unit
def test_identify_changes():
    """Test the identify_changes function."""

    # Define test content
    base_content = ["line 1", "line 2", "line 3"]
    modified_content = ["line 1", "modified line", "line 3", "line 4"]

    # Identify changes
    changes = identify_changes(base_content, modified_content)

    # Assert that the changes are correctly identified
    assert 1 in changes  # Modified line 2
    assert 3 in changes  # Added line 4
    assert changes[1] == "modified line"
    assert changes[3] == "line 4"


# Test for detect_conflicts function with no conflicts
@pytest.mark.unit
def test_detect_conflicts_no_conflicts():
    """Test the detect_conflicts function with no conflicts."""

    # Define test content
    base_content = ["line 1", "line 2", "line 3"]
    this_content = ["line 1", "modified by this", "line 3"]
    other_content = ["line 1", "line 2", "line 3", "added by other"]

    # Detect conflicts
    merged_content, conflicts = detect_conflicts(
        base_content, this_content, other_content
    )

    # Assert that there are no conflicts
    assert len(conflicts) == 0

    # Assert that the merged content contains both changes
    assert merged_content[1] == "modified by this"  # This branch's change
    assert len(merged_content) == 4  # Added line from other branch
    assert merged_content[3] == "added by other"  # Other branch's addition


# Test for detect_conflicts function with conflicts
@pytest.mark.unit
def test_detect_conflicts_with_conflicts():
    """Test the detect_conflicts function with conflicts."""

    # Define test content
    base_content = ["line 1", "line 2", "line 3"]
    this_content = ["line 1", "modified by this", "line 3"]
    other_content = ["line 1", "modified by other", "line 3"]

    # Detect conflicts
    merged_content, conflicts = detect_conflicts(
        base_content, this_content, other_content
    )

    # Assert that there is a conflict
    assert len(conflicts) == 1
    assert conflicts[0][0] == 1  # Conflict at line 2
    assert conflicts[0][1] == "modified by this"  # This branch's version
    assert conflicts[0][2] == "modified by other"  # Other branch's version

    # Assert that the merged content uses this branch's version for the conflict
    assert merged_content[1] == "modified by this"


# Test for is_binary_content function
@pytest.mark.unit
def test_is_binary_content():
    """Test the is_binary_content function."""

    # Test with text content
    text_content = b"This is text content"
    assert not is_binary_content(text_content)

    # Test with binary content (contains NUL byte)
    binary_content = b"This contains a \0 NUL byte"
    assert is_binary_content(binary_content)

    # Test with non-UTF-8 content
    non_utf8_content = b"\xff\xfe\xfd"  # Invalid UTF-8 sequence
    assert is_binary_content(non_utf8_content)


# Test for get_files_in_tree function
@pytest.mark.unit
def test_get_files_in_tree(temp_dir: pathlib.Path):
    """Test get_files_in_tree function."""

    # Initialize the repo
    repo_path = temp_dir

    # Create mock blob objects
    file1_hash = create_blob_object(repo_path, b"file1 content")
    file2_hash = create_blob_object(repo_path, b"file2 content")
    file3_hash = create_blob_object(repo_path, b"file3 content")

    # Create nested tree structure
    inner_tree_entries = [("100644", "blob", "file3.txt", file3_hash)]
    inner_tree_hash = create_tree_object(repo_path, inner_tree_entries)

    # Create outer tree with files and inner tree
    outer_tree_entries = [
        ("100644", "blob", "file1.txt", file1_hash),
        ("100644", "blob", "file2.txt", file2_hash),
        ("40000", "tree", "subdir", inner_tree_hash),
    ]
    outer_tree_hash = create_tree_object(repo_path, outer_tree_entries)

    # Test get_files_in_tree function
    files = get_files_in_tree(repo_path, outer_tree_hash)

    # Verify results
    assert len(files) == 3
    assert files["file1.txt"] == file1_hash
    assert files["file2.txt"] == file2_hash
    assert files["subdir/file3.txt"] == file3_hash

    # Test with invalid tree hash
    with patch("clony.internals.merge.read_git_object") as mock_read:
        # Mock returning non-tree object
        mock_read.return_value = ("blob", b"not a tree")

        # Should return empty dict and log error
        with patch("clony.internals.merge.logger") as mock_logger:
            result = get_files_in_tree(repo_path, "invalid_hash")
            assert result == {}
            mock_logger.error.assert_called_once()


# Test for three_way_merge function with no conflicts
@pytest.mark.unit
def test_three_way_merge_no_conflicts(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with no conflicts.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base blob objects
    base_file1_hash = create_blob_object(repo_path, b"file1 content")
    base_file2_hash = create_blob_object(repo_path, b"file2 content")

    # Create base tree object
    base_tree_entries = [
        ("100644", "blob", "file1.txt", base_file1_hash),
        ("100644", "blob", "file2.txt", base_file2_hash),
    ]
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch blob objects
    this_file1_hash = create_blob_object(repo_path, b"file1 modified by this")
    this_file2_hash = base_file2_hash  # Unchanged

    # Create this branch tree object
    this_tree_entries = [
        ("100644", "blob", "file1.txt", this_file1_hash),
        ("100644", "blob", "file2.txt", this_file2_hash),
    ]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch blob objects
    other_file1_hash = base_file1_hash  # Unchanged
    other_file2_hash = create_blob_object(repo_path, b"file2 modified by other")
    other_file3_hash = create_blob_object(repo_path, b"file3 added by other")

    # Create other branch tree object
    other_tree_entries = [
        ("100644", "blob", "file1.txt", other_file1_hash),
        ("100644", "blob", "file2.txt", other_file2_hash),
        ("100644", "blob", "file3.txt", other_file3_hash),
    ]
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Perform three-way merge
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        merge_results = three_way_merge(
            repo_path, base_commit_hash, this_commit_hash, other_commit_hash
        )

    # Assert that the merge results are correct
    assert "file1.txt" in merge_results
    assert "file2.txt" in merge_results
    assert "file3.txt" in merge_results

    # Assert that there are no conflicts
    assert len(merge_results["file1.txt"]["conflicts"]) == 0
    assert len(merge_results["file2.txt"]["conflicts"]) == 0
    assert len(merge_results["file3.txt"]["conflicts"]) == 0

    # Assert that the merged content is correct
    assert (
        "".join(merge_results["file1.txt"]["merged_content"])
        == "file1 modified by this"
    )
    assert (
        "".join(merge_results["file2.txt"]["merged_content"])
        == "file2 modified by other"
    )
    assert (
        "".join(merge_results["file3.txt"]["merged_content"]) == "file3 added by other"
    )


# Test for three_way_merge function with conflicts
@pytest.mark.unit
def test_three_way_merge_with_conflicts(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with conflicts.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base blob objects
    base_file1_hash = create_blob_object(repo_path, b"file1 content")

    # Create base tree object
    base_tree_entries = [("100644", "blob", "file1.txt", base_file1_hash)]
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch blob objects
    this_file1_hash = create_blob_object(repo_path, b"file1 modified by this")

    # Create this branch tree object
    this_tree_entries = [("100644", "blob", "file1.txt", this_file1_hash)]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch blob objects
    other_file1_hash = create_blob_object(repo_path, b"file1 modified by other")

    # Create other branch tree object
    other_tree_entries = [("100644", "blob", "file1.txt", other_file1_hash)]
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Perform three-way merge
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        merge_results = three_way_merge(
            repo_path, base_commit_hash, this_commit_hash, other_commit_hash
        )

    # Assert that the merge results are correct
    assert "file1.txt" in merge_results

    # Assert that there is a conflict
    assert len(merge_results["file1.txt"]["conflicts"]) == 1

    # Assert that the merged content uses this branch's version for the conflict
    assert (
        "".join(merge_results["file1.txt"]["merged_content"])
        == "file1 modified by this"
    )


# Test for display_merge_results function with rich console
@pytest.mark.unit
def test_display_merge_results():
    """Test display_merge_results function."""

    # Create mock merge results
    merge_results = {
        "file1.txt": {
            "merged_content": ["line 1", "line 2", "line 3"],
            "conflicts": [],
            "is_binary": False,
        },
        "file2.txt": {
            "merged_content": ["line 1", "line 2", "line 3"],
            "conflicts": [(1, "this change", "other change")],
            "is_binary": False,
        },
        "binary_file.bin": {
            "merged_content": [],
            "conflicts": [(-1, "Binary file", "Binary file")],
            "is_binary": True,
        },
    }

    # Test display_merge_results with mock console
    with patch("clony.internals.merge.console") as mock_console:
        with patch("clony.internals.merge.Table") as mock_table:
            # Mock a table instance
            mock_table_instance = mock.MagicMock()
            mock_table.return_value = mock_table_instance

            # Call display_merge_results
            num_conflicts = display_merge_results(merge_results)

            # Verify that it returns the correct number of conflicts
            assert num_conflicts == 2

            # Verify that console.print was called
            assert mock_console.print.call_count > 0

            # Verify that Table was created and add_column was called
            assert mock_table.call_count > 0
            assert mock_table_instance.add_column.call_count > 0

            # Verify table.add_row was called for each file and each conflict
            # 3 files in the main table + 2 files with conflicts in conflict tables
            assert mock_table_instance.add_row.call_count == 5


# Test for three_way_merge with files added in both branches with identical content
@pytest.mark.unit
def test_three_way_merge_added_identical_in_both(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with a file added in both branches with
    identical content.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base tree object - empty tree
    base_tree_entries = []
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch blob objects
    this_new_file_hash = create_blob_object(repo_path, b"new file content")

    # Create this branch tree object
    this_tree_entries = [("100644", "blob", "new_file.txt", this_new_file_hash)]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch blob objects - identical content
    other_new_file_hash = create_blob_object(repo_path, b"new file content")

    # Create other branch tree object
    other_tree_entries = [("100644", "blob", "new_file.txt", other_new_file_hash)]
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Perform three-way merge
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        # Perform the merge
        merge_results = three_way_merge(
            repo_path, base_commit_hash, this_commit_hash, other_commit_hash
        )

    # Assert that the merge results are correct
    assert "new_file.txt" in merge_results

    # Assert that there are no conflicts (same content in both branches)
    assert len(merge_results["new_file.txt"]["conflicts"]) == 0


# Test for three_way_merge with binary files added
@pytest.mark.unit
def test_three_way_merge_binary_file_added(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with a binary file added.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base tree object - empty tree
    base_tree_entries = []
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch blob objects - binary content
    this_binary_file_hash = create_blob_object(repo_path, b"binary\0content")

    # Create this branch tree object
    this_tree_entries = [("100644", "blob", "binary_file.bin", this_binary_file_hash)]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch tree object - no binary file
    other_tree_entries = []
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Perform three-way merge
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        # Need to patch logger to catch the warning
        with patch("clony.internals.merge.logger") as mock_logger:
            # Perform the merge
            merge_results = three_way_merge(
                repo_path, base_commit_hash, this_commit_hash, other_commit_hash
            )

            # Verify that a warning was logged for binary files
            mock_logger.warning.assert_called_with(
                "Skipping binary file: binary_file.bin"
            )

    # Assert that the merge results are correct
    assert "binary_file.bin" in merge_results
    assert merge_results["binary_file.bin"]["is_binary"] is True


# Test for three_way_merge with file added in this branch only
@pytest.mark.unit
def test_three_way_merge_file_added_in_this_branch(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with a file added only in 'this' branch.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base tree with no files
    base_tree_entries = []
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch with one file added
    this_blob_hash = create_blob_object(repo_path, b"this branch content")
    this_tree_entries = [("100644", "blob", "new_file.txt", this_blob_hash)]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch with no changes (same as base)
    other_commit_hash = base_commit_hash

    # Patch parse_commit_object to return the correct tree hashes
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, base_tree_hash),
        ]

        # Perform three-way merge
        merge_results = three_way_merge(
            repo_path, base_commit_hash, this_commit_hash, other_commit_hash
        )

    # Check results
    assert "new_file.txt" in merge_results
    assert merge_results["new_file.txt"]["conflicts"] == []
    assert merge_results["new_file.txt"]["is_binary"] is False
    assert merge_results["new_file.txt"]["merged_content"] == ["this branch content"]


# Test for three_way_merge with file added in other branch only
@pytest.mark.unit
def test_three_way_merge_file_added_in_other_branch(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with a file added only in 'other' branch.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base tree with no files
    base_tree_entries = []
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch with no changes (same as base)
    this_commit_hash = base_commit_hash

    # Create other branch with one file added
    other_blob_hash = create_blob_object(repo_path, b"other branch content")
    other_tree_entries = [("100644", "blob", "new_file.txt", other_blob_hash)]
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Patch parse_commit_object to return the correct tree hashes
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, base_tree_hash),
            (None, other_tree_hash),
        ]

        # Perform three-way merge
        merge_results = three_way_merge(
            repo_path, base_commit_hash, this_commit_hash, other_commit_hash
        )

    # Check results
    assert "new_file.txt" in merge_results
    assert merge_results["new_file.txt"]["conflicts"] == []
    assert merge_results["new_file.txt"]["is_binary"] is False
    assert merge_results["new_file.txt"]["merged_content"] == ["other branch content"]


# Test for three_way_merge with binary file added in this branch only
@pytest.mark.unit
def test_three_way_merge_binary_file_added_in_this_branch(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with a binary file added only in 'this' branch.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base tree with no files
    base_tree_entries = []
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch with one binary file added (contains null byte)
    this_blob_hash = create_blob_object(repo_path, b"binary\0content")
    this_tree_entries = [("100644", "blob", "binary_file.bin", this_blob_hash)]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch with no changes (same as base)
    other_commit_hash = base_commit_hash

    # Patch parse_commit_object to return the correct tree hashes
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, base_tree_hash),
        ]

        # Patch the logger to verify warnings
        with patch("clony.internals.merge.logger") as mock_logger:
            # Perform three-way merge
            merge_results = three_way_merge(
                repo_path, base_commit_hash, this_commit_hash, other_commit_hash
            )

            # Check that warning was logged for binary file
            mock_logger.warning.assert_called_with(
                "Skipping binary file: binary_file.bin"
            )

    # Check results - Note: binary files added in 'this' branch have conflicts=[]
    # not [(-1, 'Binary file', 'Binary file')]
    assert "binary_file.bin" in merge_results
    assert merge_results["binary_file.bin"]["conflicts"] == []
    assert merge_results["binary_file.bin"]["is_binary"] is True
    assert merge_results["binary_file.bin"]["merged_content"] == []


# Test for three_way_merge with binary file added in other branch only
@pytest.mark.unit
def test_three_way_merge_binary_file_added_in_other_branch(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with a binary file added only in 'other' branch.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base tree with no files
    base_tree_entries = []
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch with no changes (same as base)
    this_commit_hash = base_commit_hash

    # Create other branch with one binary file added (contains null byte)
    other_blob_hash = create_blob_object(repo_path, b"binary\0content")
    other_tree_entries = [("100644", "blob", "binary_file.bin", other_blob_hash)]
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Patch parse_commit_object to return the correct tree hashes
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, base_tree_hash),
            (None, other_tree_hash),
        ]

        # Patch the logger to verify warnings
        with patch("clony.internals.merge.logger") as mock_logger:
            # Perform three-way merge
            merge_results = three_way_merge(
                repo_path, base_commit_hash, this_commit_hash, other_commit_hash
            )

            # Check that warning was logged for binary file
            mock_logger.warning.assert_called_with(
                "Skipping binary file: binary_file.bin"
            )

    # Check results
    assert "binary_file.bin" in merge_results
    assert merge_results["binary_file.bin"]["conflicts"] == []
    assert merge_results["binary_file.bin"]["is_binary"] is True
    assert merge_results["binary_file.bin"]["merged_content"] == []


# Test for three_way_merge with file deleted in both branches
@pytest.mark.unit
def test_three_way_merge_file_deleted_in_both(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with a file deleted in both branches.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base blob objects
    base_file_hash = create_blob_object(repo_path, b"file content")

    # Create base tree object with the file
    base_tree_entries = [("100644", "blob", "file_to_delete.txt", base_file_hash)]
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch tree object - file deleted
    this_tree_entries = []
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch tree object - file also deleted
    other_tree_entries = []
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Perform three-way merge
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        merge_results = three_way_merge(
            repo_path, base_commit_hash, this_commit_hash, other_commit_hash
        )

    # Assert that the merge results are correct
    assert "file_to_delete.txt" in merge_results

    # Assert that the file is correctly marked as deleted with no conflicts
    assert len(merge_results["file_to_delete.txt"]["merged_content"]) == 0
    assert len(merge_results["file_to_delete.txt"]["conflicts"]) == 0


# Test for three_way_merge with file deleted in this branch but modified in other
@pytest.mark.unit
def test_three_way_merge_file_deleted_in_this_modified_in_other(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with a file deleted in this branch but
    modified in other.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base blob objects
    base_file_hash = create_blob_object(repo_path, b"file content")

    # Create base tree object with the file
    base_tree_entries = [("100644", "blob", "conflict_file.txt", base_file_hash)]
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch tree object - file deleted
    this_tree_entries = []
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch blob objects - file modified
    other_file_hash = create_blob_object(repo_path, b"modified content")

    # Create other branch tree object
    other_tree_entries = [("100644", "blob", "conflict_file.txt", other_file_hash)]
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Perform three-way merge
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        # Perform the merge
        merge_results = three_way_merge(
            repo_path, base_commit_hash, this_commit_hash, other_commit_hash
        )

    # Assert that the merge results are correct
    assert "conflict_file.txt" in merge_results

    # Assert that there is a conflict
    assert len(merge_results["conflict_file.txt"]["conflicts"]) == 1

    # Assert that the conflict is correct
    conflict = merge_results["conflict_file.txt"]["conflicts"][0]
    assert conflict[1] == "File deleted in this branch"
    assert conflict[2] == "File modified in other branch"


# Test for three_way_merge with file deleted in other branch but modified in this
@pytest.mark.unit
def test_three_way_merge_file_modified_in_this_deleted_in_other(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with a file modified in this branch but
    deleted in other.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base blob objects
    base_file_hash = create_blob_object(repo_path, b"file content")

    # Create base tree object with the file
    base_tree_entries = [("100644", "blob", "conflict_file.txt", base_file_hash)]
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch blob objects - file modified
    this_file_hash = create_blob_object(repo_path, b"modified by this branch")

    # Create this branch tree object
    this_tree_entries = [("100644", "blob", "conflict_file.txt", this_file_hash)]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch tree object - file deleted
    other_tree_entries = []
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Perform three-way merge
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        merge_results = three_way_merge(
            repo_path, base_commit_hash, this_commit_hash, other_commit_hash
        )

    # Assert that the merge results are correct
    assert "conflict_file.txt" in merge_results

    # Assert that there is a conflict
    assert len(merge_results["conflict_file.txt"]["conflicts"]) == 1

    # Assert that the conflict is correct
    conflict = merge_results["conflict_file.txt"]["conflicts"][0]
    assert conflict[1] == "File modified in this branch"
    assert conflict[2] == "File deleted in other branch"


# Test for three_way_merge with binary files in all commits
@pytest.mark.unit
def test_three_way_merge_binary_files(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with binary files in all commits.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base blob objects - binary content
    base_binary_hash = create_blob_object(repo_path, b"binary\0content")

    # Create base tree object with the binary file
    base_tree_entries = [("100644", "blob", "binary_file.bin", base_binary_hash)]
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch blob objects - modified binary file
    this_binary_hash = create_blob_object(repo_path, b"modified\0in\0this")

    # Create this branch tree object
    this_tree_entries = [("100644", "blob", "binary_file.bin", this_binary_hash)]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch blob objects - also modified binary file
    other_binary_hash = create_blob_object(repo_path, b"modified\0in\0other")

    # Create other branch tree object
    other_tree_entries = [("100644", "blob", "binary_file.bin", other_binary_hash)]
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Perform three-way merge
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        # Need to patch logger to catch the warning
        with patch("clony.internals.merge.logger") as mock_logger:
            merge_results = three_way_merge(
                repo_path, base_commit_hash, this_commit_hash, other_commit_hash
            )
            # Verify that a warning was logged for binary files
            mock_logger.warning.assert_called_with(
                "Skipping binary file: binary_file.bin"
            )

    # Assert that the merge results are correct
    assert "binary_file.bin" in merge_results
    assert merge_results["binary_file.bin"]["is_binary"] is True
    assert len(merge_results["binary_file.bin"]["conflicts"]) == 1
    assert merge_results["binary_file.bin"]["conflicts"][0][0] == -1


# Test for edge cases in detect_conflicts
@pytest.mark.unit
def test_detect_conflicts_edge_cases():
    """Test detect_conflicts function with various edge cases."""

    # Test when one file is empty
    base_content = []
    this_content = ["new line 1", "new line 2"]
    other_content = []

    # Detect conflicts
    merged_content, conflicts = detect_conflicts(
        base_content, this_content, other_content
    )

    # Should have no conflicts - this branch added content, other didn't change
    assert len(conflicts) == 0
    assert merged_content == this_content

    # Test when base is empty, both add different content
    base_content = []
    this_content = ["line added in this"]
    other_content = ["line added in other"]

    # Detect conflicts
    merged_content, conflicts = detect_conflicts(
        base_content, this_content, other_content
    )

    # Should have conflicts - both added different content
    assert len(conflicts) == 1

    # Test with a complex case - deletions and additions
    base_content = ["line 1", "line 2", "line 3", "line 4"]
    this_content = [
        "line 1",
        "modified in this",
        "line 4",
    ]  # Modified line 2, deleted line 3
    other_content = [
        "line 1",
        "line 2",
        "modified in other",
        "line 4",
    ]  # Modified line 3

    # Detect conflicts
    merged_content, conflicts = detect_conflicts(
        base_content, this_content, other_content
    )

    # No conflict since changes are in different lines
    assert len(conflicts) == 0

    # Result should have both modifications
    assert "modified in this" in merged_content
    assert "modified in other" in merged_content


# Test for edge cases where one branch made changes but the other didn't
@pytest.mark.unit
def test_detect_conflicts_one_branch_change():
    """Test detect_conflicts function when only one branch made changes."""

    # Define test content - only this branch changes line 2
    base_content = ["line 1", "line 2", "line 3"]
    this_content = ["line 1", "modified in this branch", "line 3"]
    other_content = ["line 1", "line 2", "line 3"]

    # Detect conflicts with changes only in this branch
    merged_content, conflicts = detect_conflicts(
        base_content, this_content, other_content
    )

    # Assert that there are no conflicts
    assert len(conflicts) == 0

    # Assert that the merged content contains the change from this branch
    assert merged_content[1] == "modified in this branch"

    # Test with changes only in other branch
    this_content_2 = ["line 1", "line 2", "line 3"]
    other_content_2 = ["line 1", "modified in other branch", "line 3"]

    # Detect conflicts with changes only in other branch
    merged_content_2, conflicts_2 = detect_conflicts(
        base_content, this_content_2, other_content_2
    )

    # Assert that there are no conflicts
    assert len(conflicts_2) == 0

    # Assert that the merged content contains the change from other branch
    assert merged_content_2[1] == "modified in other branch"


# Test for is_binary_content with various inputs
@pytest.mark.unit
def test_is_binary_content_comprehensive():
    """Test is_binary_content function with various inputs."""

    # Test with definitely binary content
    assert is_binary_content(b"binary\0content") is True

    # Test with binary content (contains bytes above 127)
    assert is_binary_content(bytes([0x80, 0x90, 0xA0])) is True

    # Test with text content (all bytes below 127)
    assert is_binary_content(b"This is text content") is False

    # Test with empty content (should be treated as text)
    assert is_binary_content(b"") is False

    # Test with non-printable ASCII but utf-8 decodable
    # The implementation only checks for null bytes and utf-8 decode errors
    assert is_binary_content(bytes([0x01, 0x02, 0x03])) is False

    # Test with content that has invalid UTF-8 sequence
    assert is_binary_content(b"\xff\xfe\x00\x00") is True


# Test for three_way_merge specifically focusing on file addition conflicts
@pytest.mark.unit
def test_three_way_merge_file_added_differently(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with files added differently in both branches.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base tree object - empty tree
    base_tree_entries = []
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch blob objects - new file
    this_new_file_hash = create_blob_object(repo_path, b"content in this branch")

    # Create this branch tree object
    this_tree_entries = [("100644", "blob", "new_file.txt", this_new_file_hash)]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch blob objects - different content for same file
    other_new_file_hash = create_blob_object(
        repo_path, b"different content in other branch"
    )

    # Create other branch tree object
    other_tree_entries = [("100644", "blob", "new_file.txt", other_new_file_hash)]
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Perform three-way merge
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        # Perform the merge
        merge_results = three_way_merge(
            repo_path, base_commit_hash, this_commit_hash, other_commit_hash
        )

    # Assert that the merge results are correct
    assert "new_file.txt" in merge_results

    # Assert that there is a conflict for differently added files
    assert len(merge_results["new_file.txt"]["conflicts"]) == 1

    # Assert that the conflict is correct
    conflict = merge_results["new_file.txt"]["conflicts"][0]
    assert conflict[0] == 0
    assert conflict[1] == "File added in this branch"
    assert conflict[2] == "File added in other branch"

    # The contents should be from this branch
    assert (
        "".join(merge_results["new_file.txt"]["merged_content"])
        == "content in this branch"
    )


# Test to increase coverage for perform_merge function
@pytest.mark.unit
def test_perform_merge_full(temp_dir: pathlib.Path):
    """
    Test the perform_merge function with full mocking of dependencies.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Change to the temporary directory
    original_dir = os.getcwd()
    os.chdir(temp_dir)

    try:
        # Setup repository path
        repo_path = temp_dir

        # Create mock repository
        with patch("clony.internals.merge.Repository") as mock_repo:
            # Setup mock to return current commit hash
            mock_repo_instance = mock_repo.return_value
            mock_repo_instance.get_head_commit.return_value = "current_commit_hash"

            # Mock three_way_merge function
            with patch("clony.internals.merge.three_way_merge") as mock_merge:
                # Setup mock to return merge results
                mock_merge.return_value = {
                    "file1.txt": {
                        "merged_content": ["line 1", "line 2"],
                        "conflicts": [],
                        "is_binary": False,
                    },
                    "file2.txt": {
                        "merged_content": ["line 1", "line 2"],
                        "conflicts": [(1, "this change", "other change")],
                        "is_binary": False,
                    },
                }

                # Mock display_merge_results
                with patch(
                    "clony.internals.merge.display_merge_results"
                ) as mock_display:
                    # Setup mock to return number of conflicts
                    mock_display.return_value = 1

                    # Call perform_merge
                    conflicts = perform_merge("base_hash", "other_hash")

                    # Verify that perform_merge returns the correct number of conflicts
                    assert conflicts == 1

                    # Verify three_way_merge was called with correct arguments
                    mock_merge.assert_called_once_with(
                        repo_path, "base_hash", "current_commit_hash", "other_hash"
                    )

                    # Verify display_merge_results was called with the merge results
                    mock_display.assert_called_once_with(mock_merge.return_value)
    finally:
        # Restore original directory
        os.chdir(original_dir)


# Test for three_way_merge focusing on binary file in base
@pytest.mark.unit
def test_three_way_merge_with_binary_file_in_base(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with binary file in base.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base blob objects - binary content
    base_binary_hash = create_blob_object(repo_path, b"binary\0content")

    # Create base tree object with the binary file
    base_tree_entries = [("100644", "blob", "binary_file.bin", base_binary_hash)]
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch blob objects - modified binary file
    this_binary_hash = create_blob_object(repo_path, b"modified\0in\0this")

    # Create this branch tree object
    this_tree_entries = [("100644", "blob", "binary_file.bin", this_binary_hash)]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch blob objects - now text content (edge case)
    other_text_hash = create_blob_object(repo_path, b"text content")

    # Create other branch tree object
    other_tree_entries = [("100644", "blob", "binary_file.bin", other_text_hash)]
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Perform three-way merge
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        # Need to patch logger to catch the warning
        with patch("clony.internals.merge.logger") as mock_logger:
            merge_results = three_way_merge(
                repo_path, base_commit_hash, this_commit_hash, other_commit_hash
            )
            # Verify that a warning was logged for binary files
            mock_logger.warning.assert_called_with(
                "Skipping binary file: binary_file.bin"
            )

    # Assert that the merge results are correct
    assert "binary_file.bin" in merge_results
    assert merge_results["binary_file.bin"]["is_binary"] is True


# Test for three_way_merge with invalid commit objects
@pytest.mark.unit
def test_three_way_merge_with_invalid_commit(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with invalid commit objects.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create mock parse_commit_object that raises an error
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Mock to raise ValueError on first call only
        mock_parse_commit.side_effect = [ValueError("Invalid commit object")]

        # Need to patch logger to catch the error
        with patch("clony.internals.merge.logger") as mock_logger:
            # Call three_way_merge - should raise ValueError
            with pytest.raises(ValueError):
                three_way_merge(
                    repo_path, "invalid_base", "invalid_this", "invalid_other"
                )

            # The current implementation doesn't log errors
            # This just verifies the mock was set up correctly
            assert mock_logger.error.call_count == 0


# Test for three_way_merge error handling with try/except block
@pytest.mark.unit
def test_three_way_merge_exception_handling(temp_dir: pathlib.Path):
    """
    Test that three_way_merge properly handles exceptions.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create mock objects to avoid errors before our patching takes effect
    base_blob_hash = create_blob_object(repo_path, b"base content")
    base_tree_entries = [("100644", "blob", "file.txt", base_blob_hash)]
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Now let's make sure we can handle errors in different spots during the merge

    # Test 1: Handle error when getting this branch tree
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # First call (base) succeeds, second call (this) fails
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),  # Base commit is valid
            ValueError("Invalid this commit"),  # This commit fails
        ]

        with patch("clony.internals.merge.logger") as mock_logger:
            # Call the function with try/except to catch the exception
            with pytest.raises(ValueError):
                three_way_merge(
                    repo_path, base_commit_hash, "invalid_this", "other_hash"
                )

            # The current implementation doesn't log errors
            # This just verifies the mock was set up correctly
            assert mock_logger.error.call_count == 0


# Test for get_files_in_tree with deep nesting
@pytest.mark.unit
def test_get_files_in_tree_deep_nesting(temp_dir: pathlib.Path):
    """Test get_files_in_tree function with deeply nested directories."""

    # Initialize the repo
    repo_path = temp_dir

    # Create file blobs
    file1_hash = create_blob_object(repo_path, b"file1 content")
    file2_hash = create_blob_object(repo_path, b"file2 content")
    file3_hash = create_blob_object(repo_path, b"file3 content")

    # Create deepest tree
    deepest_tree_entries = [("100644", "blob", "file3.txt", file3_hash)]
    deepest_tree_hash = create_tree_object(repo_path, deepest_tree_entries)

    # Create middle tree
    middle_tree_entries = [
        ("100644", "blob", "file2.txt", file2_hash),
        ("40000", "tree", "level3", deepest_tree_hash),
    ]
    middle_tree_hash = create_tree_object(repo_path, middle_tree_entries)

    # Create root tree
    root_tree_entries = [
        ("100644", "blob", "file1.txt", file1_hash),
        ("40000", "tree", "level2", middle_tree_hash),
    ]
    root_tree_hash = create_tree_object(repo_path, root_tree_entries)

    # Test get_files_in_tree with deep nesting
    files = get_files_in_tree(repo_path, root_tree_hash)

    # Verify results
    assert len(files) == 3
    assert files["file1.txt"] == file1_hash
    assert files["level2/file2.txt"] == file2_hash
    assert files["level2/level3/file3.txt"] == file3_hash

    # Also test that it handles recursive paths correctly
    assert all(isinstance(path, str) for path in files.keys())


# Test for three_way_merge with mixed content types in different branches
@pytest.mark.unit
def test_three_way_merge_mixed_content_types(temp_dir: pathlib.Path):
    """
    Test the three_way_merge function with mixed content types in different branches.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize the repo
    repo_path = temp_dir

    # Create base blob objects - text content
    base_text_hash = create_blob_object(repo_path, b"text content")

    # Create base tree object with the text file
    base_tree_entries = [("100644", "blob", "file.txt", base_text_hash)]
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch blob objects - modified to binary
    this_binary_hash = create_blob_object(repo_path, b"binary\0content")

    # Create this branch tree object
    this_tree_entries = [("100644", "blob", "file.txt", this_binary_hash)]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch blob objects - modified text content
    other_text_hash = create_blob_object(repo_path, b"modified text content")

    # Create other branch tree object
    other_tree_entries = [("100644", "blob", "file.txt", other_text_hash)]
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Perform three-way merge
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        # Configure the mock to return tree hashes
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        # Need to patch logger to catch the warning
        with patch("clony.internals.merge.logger") as mock_logger:
            merge_results = three_way_merge(
                repo_path, base_commit_hash, this_commit_hash, other_commit_hash
            )
            # Verify that a warning was logged for binary files
            mock_logger.warning.assert_called_with("Skipping binary file: file.txt")

    # Assert that the merge results are correct
    assert "file.txt" in merge_results
    assert merge_results["file.txt"]["is_binary"] is True


# Test for complex three_way_merge scenarios with line appending
@pytest.mark.unit
def test_three_way_merge_complex_line_operations(temp_dir: pathlib.Path):
    """
    Test complex scenarios in detect_conflicts with line appending operations.
    This tests the specific code paths where lines need to be appended rather than
    modified.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Test direct detect_conflicts function to ensure coverage
    # Case 1: Both branches make identical changes that need appending
    base_lines = ["line 1", "line 2"]
    this_lines = ["line 1", "line 2", "line 3 added by this"]
    other_lines = ["line 1", "line 2", "line 3 added by this"]  # Same addition

    merged_content, conflicts = detect_conflicts(base_lines, this_lines, other_lines)
    assert conflicts == []
    assert len(merged_content) == 3
    assert merged_content[2] == "line 3 added by this"

    # Case 2: Branches make different changes that need appending
    base_lines = ["line 1", "line 2"]
    this_lines = ["line 1", "line 2", "line 3 added by this"]
    other_lines = ["line 1", "line 2", "line 3 added by other"]  # Different addition

    merged_content, conflicts = detect_conflicts(base_lines, this_lines, other_lines)
    assert len(conflicts) == 1
    assert conflicts[0][0] == 2  # Conflict at line index 2
    assert conflicts[0][1] == "line 3 added by this"
    assert conflicts[0][2] == "line 3 added by other"
    assert len(merged_content) == 3
    # This branch's version should be kept for conflicts
    assert merged_content[2] == "line 3 added by this"

    # Case 3: Only this branch changes a line that needs appending
    base_lines = ["line 1", "line 2"]
    this_lines = ["line 1", "line 2", "line 3 added by this"]
    other_lines = ["line 1", "line 2"]  # No addition

    merged_content, conflicts = detect_conflicts(base_lines, this_lines, other_lines)
    assert conflicts == []
    assert len(merged_content) == 3
    assert merged_content[2] == "line 3 added by this"

    # Case 4: Only other branch changes a line that needs appending
    base_lines = ["line 1", "line 2"]
    this_lines = ["line 1", "line 2"]  # No addition
    other_lines = ["line 1", "line 2", "line 3 added by other"]

    merged_content, conflicts = detect_conflicts(base_lines, this_lines, other_lines)
    assert conflicts == []
    assert len(merged_content) == 3
    assert merged_content[2] == "line 3 added by other"

    # Case 5: Same changes to non-consecutive lines (specific test for line 112)
    base_lines = ["line 1", "line 2", "line 3"]
    this_lines = ["line 1", "modified line 2", "line 3"]
    other_lines = ["line 1", "modified line 2", "line 3"]

    merged_content, conflicts = detect_conflicts(base_lines, this_lines, other_lines)
    assert conflicts == []
    assert len(merged_content) == 3
    assert merged_content[1] == "modified line 2"

    # Test the specific binary file comparison in both branches
    # First with exact same files in repo structure
    repo_path = temp_dir

    # Create base blob objects - text content
    base_blob_hash = create_blob_object(repo_path, b"text content")

    # Create base tree object with the text file
    base_tree_entries = [("100644", "blob", "file.txt", base_blob_hash)]
    base_tree_hash = create_tree_object(repo_path, base_tree_entries)

    # Create base commit
    base_commit_hash = create_commit_object(repo_path, base_tree_hash)

    # Create this branch blob objects - binary content
    this_binary_hash = create_blob_object(repo_path, b"binary\0content")

    # Create this branch tree object
    this_tree_entries = [("100644", "blob", "file.txt", this_binary_hash)]
    this_tree_hash = create_tree_object(repo_path, this_tree_entries)

    # Create this branch commit
    this_commit_hash = create_commit_object(repo_path, this_tree_hash, base_commit_hash)

    # Create other branch blob objects - same binary content as this branch
    other_binary_hash = (
        this_binary_hash  # Using same hash to simulate exact same content
    )

    # Create other branch tree object
    other_tree_entries = [("100644", "blob", "file.txt", other_binary_hash)]
    other_tree_hash = create_tree_object(repo_path, other_tree_entries)

    # Create other branch commit
    other_commit_hash = create_commit_object(
        repo_path, other_tree_hash, base_commit_hash
    )

    # Patch logger to verify warning
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash),
            (None, other_tree_hash),
        ]

        with patch("clony.internals.merge.logger") as mock_logger:
            # Perform three-way merge
            merge_results = three_way_merge(
                repo_path, base_commit_hash, this_commit_hash, other_commit_hash
            )

            # Verify warning was logged
            mock_logger.warning.assert_called_with("Skipping binary file: file.txt")

    # Check binary file conflict handling when in both branches
    assert "file.txt" in merge_results
    assert merge_results["file.txt"]["conflicts"] == [
        (-1, "Binary file", "Binary file")
    ]
    assert merge_results["file.txt"]["is_binary"] is True
    assert merge_results["file.txt"]["merged_content"] == []

    # Now test with different binary content in each branch
    # Create new different binary content for both branches
    this_binary_hash2 = create_blob_object(repo_path, b"binary\0content in this branch")
    other_binary_hash2 = create_blob_object(
        repo_path, b"different\0binary in other branch"
    )

    # Create this branch tree object
    this_tree_entries2 = [("100644", "blob", "binary_file.bin", this_binary_hash2)]
    this_tree_hash2 = create_tree_object(repo_path, this_tree_entries2)

    # Create this branch commit
    this_commit_hash2 = create_commit_object(
        repo_path, this_tree_hash2, base_commit_hash
    )

    # Create other branch tree object
    other_tree_entries2 = [("100644", "blob", "binary_file.bin", other_binary_hash2)]
    other_tree_hash2 = create_tree_object(repo_path, other_tree_entries2)

    # Create other branch commit
    other_commit_hash2 = create_commit_object(
        repo_path, other_tree_hash2, base_commit_hash
    )

    # Patch logger to verify warning
    with patch("clony.internals.merge.parse_commit_object") as mock_parse_commit:
        mock_parse_commit.side_effect = [
            (None, base_tree_hash),
            (None, this_tree_hash2),
            (None, other_tree_hash2),
        ]

        with patch("clony.internals.merge.logger") as mock_logger:
            # Perform three-way merge
            merge_results = three_way_merge(
                repo_path, base_commit_hash, this_commit_hash2, other_commit_hash2
            )

            # Verify warning was logged
            mock_logger.warning.assert_called_with(
                "Skipping binary file: binary_file.bin"
            )

    # Check binary file conflict handling when in both branches
    assert "binary_file.bin" in merge_results
    assert merge_results["binary_file.bin"]["conflicts"] == [
        (-1, "Binary file", "Binary file")
    ]
    assert merge_results["binary_file.bin"]["is_binary"] is True
    assert merge_results["binary_file.bin"]["merged_content"] == []
