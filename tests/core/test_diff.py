"""
Tests for the diff functionality.

This module contains tests for the diff module, which is used to compute
differences between blob objects.
"""

# Standard library imports
import hashlib
import importlib
import pathlib
import shutil
import sys
import tempfile
import zlib
from typing import Generator
from unittest.mock import patch

# Third-party imports
import pytest
from colorama import Fore

# Local imports
from clony.core.diff import (
    colorize_diff_line,
    colorize_unified_diff_line,
    diff_blobs,
    generate_unified_diff,
    is_binary_content,
    myers_diff,
    print_diff,
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

    # Yield the temporary directory path
    yield temp_path

    # Clean up the temporary directory
    shutil.rmtree(temp_path)


# Function to create a test object
def create_test_object(
    temp_dir: pathlib.Path, content: bytes, object_type: str = "blob"
) -> str:
    """
    Create a test object for testing.

    Args:
        temp_dir (pathlib.Path): The temporary directory.
        content (bytes): The content of the object.
        object_type (str, optional): The type of the object. Defaults to "blob".

    Returns:
        str: The SHA-1 hash of the object.
    """

    # Prepare the object content with header
    header = f"{object_type} {len(content)}\0".encode()
    store_content = header + content

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

    # Return the SHA-1 hash
    return sha1_hash


# Test for read_git_object function
@pytest.mark.unit
def test_read_git_object(temp_dir: pathlib.Path):
    """
    Test the read_git_object function.
    """

    # Create a test object
    content = b"test content"
    object_type = "blob"
    sha1_hash = create_test_object(temp_dir, content, object_type)

    # Read the object
    read_type, read_content = read_git_object(temp_dir, sha1_hash)

    # Assert that the read type and content match the original
    assert read_type == object_type
    assert read_content == content


# Test for read_git_object function with non-existing object
@pytest.mark.unit
def test_read_git_object_non_existing(temp_dir: pathlib.Path):
    """
    Test the read_git_object function with a non-existing object.
    """

    # Read a non-existing object
    object_type, content = read_git_object(temp_dir, "nonexistent")

    # Assert that the read type and content are empty
    assert object_type == ""
    assert content == b""


# Test for myers_diff function
@pytest.mark.unit
def test_myers_diff():
    """
    Test the myers_diff function.
    """

    # Define test input
    a = ["line 1", "line 2", "line 3", "line 4"]
    b = ["line 1", "modified line", "line 3", "line 5"]

    # Calculate the diff
    diff = myers_diff(a, b)

    # Define expected output
    expected = [
        (" ", "line 1"),
        ("-", "line 2"),
        ("+", "modified line"),
        (" ", "line 3"),
        ("-", "line 4"),
        ("+", "line 5"),
    ]

    # Assert that the diff matches the expected output
    assert diff == expected


# Test for myers_diff function with empty lists
@pytest.mark.unit
def test_myers_diff_empty():
    """
    Test the myers_diff function with empty lists.
    """

    # Define test input
    a = []
    b = []

    # Calculate the diff
    diff = myers_diff(a, b)

    # Define expected output
    expected = []

    # Assert that the diff matches the expected output
    assert diff == expected


# Test for myers_diff function with delete-only and insert-only scenarios
@pytest.mark.unit
def test_myers_diff_delete_insert():
    """
    Test the myers_diff function with delete-only and insert-only scenarios.
    """

    # Test delete-only scenario
    a_delete = ["line 1", "line 2", "line 3"]
    b_delete = ["line 1", "line 3"]
    diff_delete = myers_diff(a_delete, b_delete)

    # Expected output for delete-only
    expected_delete = [
        (" ", "line 1"),
        ("-", "line 2"),
        (" ", "line 3"),
    ]
    assert diff_delete == expected_delete

    # Test insert-only scenario
    a_insert = ["line 1", "line 3"]
    b_insert = ["line 1", "line 2", "line 3"]
    diff_insert = myers_diff(a_insert, b_insert)

    # Expected output for insert-only
    expected_insert = [
        (" ", "line 1"),
        ("+", "line 2"),
        (" ", "line 3"),
    ]
    assert diff_insert == expected_insert


# Test for colorize_diff_line function
@pytest.mark.unit
def test_colorize_diff_line():
    """
    Test the colorize_diff_line function.
    """

    # Define test input
    line1 = ("+", "added line")
    line2 = ("-", "deleted line")
    line3 = (" ", "unchanged line")

    # Colorize the lines
    result1 = colorize_diff_line(line1)
    result2 = colorize_diff_line(line2)
    result3 = colorize_diff_line(line3)

    # Check that the output contains the expected content
    assert "added line" in result1
    assert "deleted line" in result2
    assert "unchanged line" in result3


# Test for colorize_diff_line function without color support
@pytest.mark.unit
def test_colorize_diff_line_no_color():
    """
    Test the colorize_diff_line function without color support.
    """

    # Mock the COLOR_SUPPORT variable to be False
    with patch("clony.core.diff.COLOR_SUPPORT", False):
        # Define test input
        line1 = ("+", "added line")
        line2 = ("-", "deleted line")
        line3 = (" ", "unchanged line")

        # Colorize the lines
        result1 = colorize_diff_line(line1)
        result2 = colorize_diff_line(line2)
        result3 = colorize_diff_line(line3)

        # Check that the output matches the expected format
        assert result1 == "+ added line"
        assert result2 == "- deleted line"
        assert result3 == "  unchanged line"


# Test for colorize_unified_diff_line function
@pytest.mark.unit
def test_colorize_unified_diff_line():
    """
    Test the colorize_unified_diff_line function.
    """

    # Mock color support to be True for this test
    with patch("clony.core.diff.COLOR_SUPPORT", True):
        # Define test input
        line1 = "+added line"
        line2 = "-deleted line"
        line3 = " unchanged line"  # Context line
        line4 = "@@ -1,3 +1,3 @@"
        line5 = "--- a/file1"
        line6 = "+++ b/file2"
        line7 = ""  # Empty line
        line8 = "some other text"  # Other non-special line

        # Colorize the lines
        result1 = colorize_unified_diff_line(line1)
        result2 = colorize_unified_diff_line(line2)
        result3 = colorize_unified_diff_line(line3)
        result4 = colorize_unified_diff_line(line4)
        result5 = colorize_unified_diff_line(line5)
        result6 = colorize_unified_diff_line(line6)
        result7 = colorize_unified_diff_line(line7)
        result8 = colorize_unified_diff_line(line8)

        # Check that the output contains the expected content
        assert "added line" in result1
        assert f"{Fore.GREEN}" in result1
        assert "deleted line" in result2
        assert f"{Fore.RED}" in result2
        assert "unchanged line" in result3
        assert "@@ -1,3 +1,3 @@" in result4
        assert f"{Fore.CYAN}" in result4

        # File headers should be BLUE
        assert "--- a/file1" in result5
        assert f"{Fore.BLUE}" in result5

        assert "+++ b/file2" in result6
        assert f"{Fore.BLUE}" in result6

        assert result7 == ""
        assert result8 == "some other text"


# Test for colorize_unified_diff_line function without color support
@pytest.mark.unit
def test_colorize_unified_diff_line_no_color():
    """
    Test the colorize_unified_diff_line function without color support.
    """

    # Mock the COLOR_SUPPORT variable to be False
    with patch("clony.core.diff.COLOR_SUPPORT", False):
        # Define test input
        line1 = "+added line"
        line2 = "-deleted line"
        line3 = " unchanged line"
        line4 = "@@ -1,3 +1,3 @@"
        line5 = "--- a/file1"
        line6 = "+++ b/file2"

        # Colorize the lines
        result1 = colorize_unified_diff_line(line1)
        result2 = colorize_unified_diff_line(line2)
        result3 = colorize_unified_diff_line(line3)
        result4 = colorize_unified_diff_line(line4)
        result5 = colorize_unified_diff_line(line5)
        result6 = colorize_unified_diff_line(line6)

        # Check that the output matches the expected format
        assert result1 == "+added line"
        assert result2 == "-deleted line"
        assert result3 == " unchanged line"
        assert result4 == "@@ -1,3 +1,3 @@"
        assert result5 == "--- a/file1"
        assert result6 == "+++ b/file2"


# Test for colorama import error scenario
@pytest.mark.unit
def test_colorama_import_error():
    """
    Test the scenario where colorama is not available.
    """

    # Save the original modules
    original_modules = sys.modules.copy()

    # Mock the import to raise ImportError for colorama
    with patch.dict(sys.modules, {"colorama": None}):
        # Force reload the diff module to trigger the ImportError
        import clony.core.diff

        importlib.reload(clony.core.diff)

        # Check that COLOR_SUPPORT is set to False
        assert clony.core.diff.COLOR_SUPPORT is False

        # Test colorize_diff_line without color support
        line = ("+", "added line")
        result = clony.core.diff.colorize_diff_line(line)
        assert result == "+ added line"

    # Restore the original modules
    sys.modules = original_modules

    # Reload the diff module to restore COLOR_SUPPORT
    importlib.reload(clony.core.diff)


# Test for generate_unified_diff function
@pytest.mark.unit
def test_generate_unified_diff():
    """
    Test the generate_unified_diff function.
    """

    # Define test input
    a_lines = ["line 1", "line 2", "line 3", "line 4"]
    b_lines = ["line 1", "modified line", "line 3", "line 5"]

    # Generate the unified diff
    diff = generate_unified_diff(a_lines, b_lines, "a", "b", 2)

    # Check that the diff contains the expected headers
    assert diff[0].startswith("---")
    assert diff[1].startswith("+++")
    assert "@@ " in diff[2]

    # Check that the diff contains the modified lines
    assert "-line 2" in diff
    assert "+modified line" in diff
    assert "-line 4" in diff
    assert "+line 5" in diff


# Test for is_binary_content function
@pytest.mark.unit
def test_is_binary_content():
    """
    Test the is_binary_content function.
    """

    # Test with binary content (null byte)
    assert is_binary_content(b"\x00\x01\x02\x03") is True

    # Test with binary content (non-UTF-8 decodable)
    assert is_binary_content(b"\xff\xfe\xfd\xfc") is True

    # Test with text content
    assert is_binary_content(b"text content") is False


# Test for diff_blobs function
@pytest.mark.unit
def test_diff_blobs(temp_dir: pathlib.Path):
    """
    Test the diff_blobs function.
    """

    # Create test objects
    content1 = b"line 1\nline 2\nline 3\nline 4"
    content2 = b"line 1\nmodified line\nline 3\nline 5"
    blob1_hash = create_test_object(temp_dir, content1)
    blob2_hash = create_test_object(temp_dir, content2)

    # Generate the diff with the myers algorithm
    diff = diff_blobs(temp_dir, blob1_hash, blob2_hash, algorithm="myers")

    # Check that the diff contains the expected content
    assert any("line 1" in line for line in diff)
    assert any("modified line" in line for line in diff)

    # Generate the diff with the unified algorithm
    diff = diff_blobs(temp_dir, blob1_hash, blob2_hash, algorithm="unified")

    # Check that the diff contains the expected headers and content
    assert "---" in diff[0]
    assert "+++" in diff[1]
    assert "@@" in diff[2]
    assert any("-line 2" in line for line in diff)
    assert any("+modified line" in line for line in diff)


# Test for diff_blobs function with custom paths
@pytest.mark.unit
def test_diff_blobs_custom_paths(temp_dir: pathlib.Path):
    """
    Test the diff_blobs function with custom paths.
    """

    # Create test objects
    content1 = b"line 1\nline 2\nline 3\nline 4"
    content2 = b"line 1\nmodified line\nline 3\nline 5"
    blob1_hash = create_test_object(temp_dir, content1)
    blob2_hash = create_test_object(temp_dir, content2)

    # Generate the diff with custom paths
    diff = diff_blobs(
        temp_dir,
        blob1_hash,
        blob2_hash,
        path1="file1.txt",
        path2="file2.txt",
        algorithm="unified",
    )

    # Check that the diff contains the expected headers
    assert "---" in diff[0]
    assert "file1.txt" in diff[0]
    assert "+++" in diff[1]
    assert "file2.txt" in diff[1]


# Test for diff_blobs function with non-existing blob
@pytest.mark.unit
def test_diff_blobs_non_existing(temp_dir: pathlib.Path):
    """
    Test the diff_blobs function with a non-existing blob.
    """

    # Create a test object
    content = b"test content"
    blob_hash = create_test_object(temp_dir, content)

    # Generate the diff with a non-existing blob
    diff = diff_blobs(temp_dir, blob_hash, "nonexistent")

    # Check that the diff is empty
    assert diff == []


# Test for diff_blobs function with non-blob objects
@pytest.mark.unit
def test_diff_blobs_non_blob(temp_dir: pathlib.Path):
    """
    Test the diff_blobs function with non-blob objects.
    """

    # Create a test object with type 'tree'
    content = b"test content"
    tree_hash = create_test_object(temp_dir, content, "tree")

    # Create a test blob object
    blob_hash = create_test_object(temp_dir, content)

    # Generate the diff with a non-blob object
    diff = diff_blobs(temp_dir, tree_hash, blob_hash)

    # Check that the diff is empty
    assert diff == []


# Test for diff_blobs function with binary content
@pytest.mark.unit
def test_diff_blobs_binary(temp_dir: pathlib.Path):
    """
    Test the diff_blobs function with binary content.
    """

    # Create test objects with binary content
    content1 = b"\x00\x01\x02\x03"
    content2 = b"\x00\x01\x02\x04"
    blob1_hash = create_test_object(temp_dir, content1)
    blob2_hash = create_test_object(temp_dir, content2)

    # Generate the diff
    diff = diff_blobs(temp_dir, blob1_hash, blob2_hash)

    # Check that the diff indicates binary files
    assert diff == ["Binary files differ"]


# Test for print_diff function
@pytest.mark.unit
def test_print_diff(temp_dir: pathlib.Path, capsys):
    """
    Test the print_diff function with the capsys fixture to capture stdout.
    """

    # Create test objects
    content1 = b"line 1\nline 2\nline 3\nline 4"
    content2 = b"line 1\nmodified line\nline 3\nline 5"
    blob1_hash = create_test_object(temp_dir, content1)
    blob2_hash = create_test_object(temp_dir, content2)

    # Call print_diff
    print_diff(temp_dir, blob1_hash, blob2_hash)

    # Capture stdout
    captured = capsys.readouterr()

    # Check that the output contains the expected content
    assert "line 1" in captured.out
    assert "modified line" in captured.out
