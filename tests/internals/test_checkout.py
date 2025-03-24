"""
Tests for the checkout module functionality.
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
from clony.internals.checkout import (
    detect_conflicts,
    display_checkout_info,
    display_conflicts,
    extract_blob_to_working_dir,
    get_commit_tree_hash,
    get_files_from_tree,
    restore_files,
    restore_specific_files,
    switch_branch_or_commit,
    update_working_dir_to_tree,
)
from clony.internals.status import FileStatus


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


# Test the detect_conflicts function
@patch("clony.internals.checkout.get_repository_status")
@patch("clony.internals.checkout.get_commit_tree_hash")
@patch("clony.internals.checkout.get_files_from_tree")
def test_detect_conflicts(
    mock_get_files_from_tree,
    mock_get_commit_tree_hash,
    mock_get_repository_status,
    temp_dir: pathlib.Path,
):
    """
    Test that detect_conflicts correctly identifies conflicts.
    """

    # Setup mocks
    repo_path = temp_dir
    target_commit = "abcdef1234567890"

    # Mock status with modified and deleted files
    mock_get_repository_status.return_value = {
        FileStatus.MODIFIED: ["file1.txt", "file2.txt"],
        FileStatus.DELETED: ["file3.txt"],
    }

    # Mock tree hash
    mock_get_commit_tree_hash.return_value = "tree123"

    # Mock files in the target commit
    mock_get_files_from_tree.return_value = {
        "file1.txt": "blob1",
        "file3.txt": "blob3",
        "file4.txt": "blob4",
    }

    # Call the function
    conflicts = detect_conflicts(repo_path, target_commit)

    # Assert that the conflicts were detected correctly
    assert len(conflicts) == 2
    assert conflicts["file1.txt"] == "modified"
    assert conflicts["file3.txt"] == "deleted"


# Test the get_commit_tree_hash function
@patch("clony.internals.checkout.read_git_object")
def test_get_commit_tree_hash(
    mock_read_git_object,
    temp_dir: pathlib.Path,
):
    """
    Test that get_commit_tree_hash correctly extracts the tree hash.
    """

    # Setup mock
    repo_path = temp_dir
    commit_hash = "abcdef1234567890"
    tree_hash = "tree1234567890abcdef"

    # Mock read_git_object to return a commit object
    mock_read_git_object.return_value = (
        "commit",
        (
            f"tree {tree_hash}\nauthor Some One <someone@example.com> "
            f"123456 +0000\n\nCommit message"
        ).encode(),
    )

    # Call the function
    result = get_commit_tree_hash(repo_path, commit_hash)

    # Assert the result
    assert result == tree_hash
    mock_read_git_object.assert_called_once_with(repo_path, commit_hash)


# Test the get_files_from_tree function
@patch("clony.internals.checkout.read_git_object")
@patch("clony.internals.checkout.parse_tree_object")
def test_get_files_from_tree(
    mock_parse_tree_object,
    mock_read_git_object,
    temp_dir: pathlib.Path,
):
    """
    Test that get_files_from_tree correctly builds a file mapping.
    """

    # Setup mocks
    repo_path = temp_dir
    tree_hash = "tree1234"

    # Mock parse_tree_object to return tree entries
    # Format: (mode, obj_type, sha1_hash, name)
    mock_parse_tree_object.return_value = [
        ("100644", "blob", "blob1", "file1.txt"),
        ("100644", "blob", "blob2", "file2.txt"),
        ("40000", "tree", "subtree1", "dir1"),
    ]

    # Mock read_git_object for the main tree and subtree
    mock_read_git_object.side_effect = [
        ("tree", b"tree content"),  # Main tree
        ("tree", b"subtree content"),  # Subtree
    ]

    # Mock get_files_from_tree recursively for the subtree
    with patch(
        "clony.internals.checkout.get_files_from_tree",
        side_effect=[
            {
                "file1.txt": "blob1",
                "file2.txt": "blob2",
                "dir1/file3.txt": "blob3",
                "dir1/file4.txt": "blob4",
            },  # Result
            {"file3.txt": "blob3", "file4.txt": "blob4"},  # Nested call result
        ],
    ):
        # Call the function
        result = get_files_from_tree(repo_path, tree_hash)

    # Assert the files were mapped correctly
    assert len(result) == 4
    assert result["file1.txt"] == "blob1"
    assert result["file2.txt"] == "blob2"
    assert result["dir1/file3.txt"] == "blob3"
    assert result["dir1/file4.txt"] == "blob4"


# Test the extract_blob_to_working_dir function
@patch("clony.internals.checkout.read_git_object")
def test_extract_blob_to_working_dir(
    mock_read_git_object,
    temp_dir: pathlib.Path,
):
    """
    Test that extract_blob_to_working_dir writes the blob content to a file.
    """

    # Setup mocks
    repo_path = temp_dir
    blob_hash = "blob123"
    file_path = "test_file.txt"
    blob_content = b"Test content for blob"

    # Mock read_git_object to return a blob
    mock_read_git_object.return_value = ("blob", blob_content)

    # Call the function
    result = extract_blob_to_working_dir(repo_path, blob_hash, file_path)

    # Assert the result and file content
    assert result is True
    full_path = repo_path / file_path
    assert full_path.exists()
    with open(full_path, "rb") as f:
        assert f.read() == blob_content


# Test the update_working_dir_to_tree function
@patch("clony.internals.checkout.get_files_from_tree")
@patch("clony.internals.checkout.extract_blob_to_working_dir")
def test_update_working_dir_to_tree(
    mock_extract_blob_to_working_dir,
    mock_get_files_from_tree,
    temp_dir: pathlib.Path,
):
    """
    Test that update_working_dir_to_tree updates all files from a tree.
    """

    # Setup mocks
    repo_path = temp_dir
    tree_hash = "tree123"

    # Mock get_files_from_tree to return file mapping
    mock_get_files_from_tree.return_value = {
        "file1.txt": "blob1",
        "file2.txt": "blob2",
        "dir1/file3.txt": "blob3",
    }

    # Mock extract_blob_to_working_dir to succeed
    mock_extract_blob_to_working_dir.return_value = True

    # Call the function
    result = update_working_dir_to_tree(repo_path, tree_hash)

    # Assert the result
    assert result is True
    assert mock_extract_blob_to_working_dir.call_count == 3


# Test the switch_branch_or_commit function with a branch
@patch("clony.internals.checkout.find_git_repo_path")
@patch("clony.internals.checkout.get_ref_hash")
@patch("clony.internals.checkout.detect_conflicts")
@patch("clony.internals.checkout.get_commit_tree_hash")
@patch("clony.internals.checkout.get_files_from_tree")
@patch("clony.internals.checkout.update_index_to_commit")
@patch("clony.internals.checkout.update_working_dir_to_tree")
@patch("clony.internals.checkout.display_checkout_info")
def test_switch_branch(
    mock_display_checkout_info,
    mock_update_working_dir_to_tree,
    mock_update_index_to_commit,
    mock_get_files_from_tree,
    mock_get_commit_tree_hash,
    mock_detect_conflicts,
    mock_get_ref_hash,
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that switch_branch_or_commit switches to a branch correctly.
    """

    # Setup mocks
    repo_path = temp_dir
    mock_find_git_repo_path.return_value = repo_path

    # Create .git directory and HEAD file
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True)

    # Mock branch reference
    branch_name = "main"
    commit_hash = "abcdef1234567890"
    mock_get_ref_hash.return_value = commit_hash

    # Mock no conflicts
    mock_detect_conflicts.return_value = {}

    # Mock tree hash
    tree_hash = "tree123"
    mock_get_commit_tree_hash.return_value = tree_hash

    # Mock file list
    mock_get_files_from_tree.return_value = {"file1.txt": "blob1", "file2.txt": "blob2"}

    # Mock successful updates
    mock_update_index_to_commit.return_value = True
    mock_update_working_dir_to_tree.return_value = True

    # Call the function
    result = switch_branch_or_commit(branch_name)

    # Assert the result
    assert result is True

    # Check HEAD file was updated
    head_file = git_dir / "HEAD"
    assert head_file.exists()
    with open(head_file, "r") as f:
        assert f.read().strip() == f"ref: refs/heads/{branch_name}"

    # Verify mock calls
    mock_update_index_to_commit.assert_called_once_with(repo_path, commit_hash)
    mock_update_working_dir_to_tree.assert_called_once_with(repo_path, tree_hash)
    mock_display_checkout_info.assert_called_once_with(branch_name, True, False, 2)


# Test the restore_files function
@patch("clony.internals.checkout.find_git_repo_path")
@patch("clony.internals.checkout.get_head_commit")
@patch("clony.internals.checkout.detect_conflicts")
@patch("clony.internals.checkout.restore_specific_files")
def test_restore_files(
    mock_restore_specific_files,
    mock_detect_conflicts,
    mock_get_head_commit,
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that restore_files restores files from HEAD.
    """

    # Setup mocks
    repo_path = temp_dir
    mock_find_git_repo_path.return_value = repo_path

    # Mock HEAD commit
    commit_hash = "abcdef1234567890"
    mock_get_head_commit.return_value = commit_hash

    # Mock no conflicts
    mock_detect_conflicts.return_value = {}

    # Mock successful restore
    mock_restore_specific_files.return_value = True

    # Call the function with file paths
    file_paths = ["file1.txt", "file2.txt"]
    result = restore_files(file_paths)

    # Assert the result
    assert result is True

    # Verify mock calls
    mock_detect_conflicts.assert_called_once_with(repo_path, commit_hash, file_paths)
    mock_restore_specific_files.assert_called_once_with(
        repo_path, commit_hash, file_paths
    )


# Test error handling in get_commit_tree_hash
@patch("clony.internals.checkout.read_git_object")
def test_get_commit_tree_hash_errors(
    mock_read_git_object,
    temp_dir: pathlib.Path,
):
    """
    Test that get_commit_tree_hash handles errors properly.
    """

    # Setup mocks
    repo_path = temp_dir
    commit_hash = "abcdef1234567890"

    # Test case 1: Not a commit object
    mock_read_git_object.return_value = ("blob", b"blob content")

    # Call the function
    result = get_commit_tree_hash(repo_path, commit_hash)

    # Assert result is None
    assert result is None

    # Test case 2: No tree hash found
    mock_read_git_object.return_value = (
        "commit",
        b"author Some One <someone@example.com> 123456 +0000\n\nCommit message",
    )

    # Call the function
    result = get_commit_tree_hash(repo_path, commit_hash)

    # Assert result is None
    assert result is None

    # Test case 3: Exception during read
    mock_read_git_object.side_effect = Exception("Test error")

    # Call the function
    result = get_commit_tree_hash(repo_path, commit_hash)

    # Assert result is None
    assert result is None


# Test error handling in get_files_from_tree
@patch("clony.internals.checkout.read_git_object")
def test_get_files_from_tree_errors(
    mock_read_git_object,
    temp_dir: pathlib.Path,
):
    """
    Test that get_files_from_tree handles errors properly.
    """

    # Setup mocks
    repo_path = temp_dir
    tree_hash = "tree1234"

    # Test case 1: Not a tree object
    mock_read_git_object.return_value = ("blob", b"blob content")

    # Call the function
    result = get_files_from_tree(repo_path, tree_hash)

    # Assert empty dict
    assert result == {}

    # Test case 2: Exception during read
    mock_read_git_object.side_effect = Exception("Test error")

    # Call the function
    result = get_files_from_tree(repo_path, tree_hash)

    # Assert empty dict
    assert result == {}


# Test error handling in extract_blob_to_working_dir
@patch("clony.internals.checkout.read_git_object")
def test_extract_blob_to_working_dir_errors(
    mock_read_git_object,
    temp_dir: pathlib.Path,
):
    """
    Test that extract_blob_to_working_dir handles errors properly.
    """

    # Setup mocks
    repo_path = temp_dir
    blob_hash = "blob123"
    file_path = "test_file.txt"

    # Test case 1: Not a blob object
    mock_read_git_object.return_value = ("tree", b"tree content")

    # Call the function
    result = extract_blob_to_working_dir(repo_path, blob_hash, file_path)

    # Assert result is False
    assert result is False

    # Test case 2: Exception during file write
    mock_read_git_object.return_value = ("blob", b"blob content")

    # Patch open to raise an exception
    with patch("builtins.open", side_effect=Exception("Test error")):
        # Call the function
        result = extract_blob_to_working_dir(repo_path, blob_hash, file_path)

        # Assert result is False
        assert result is False


# Test error handling in update_working_dir_to_tree
@patch("clony.internals.checkout.get_files_from_tree")
@patch("clony.internals.checkout.extract_blob_to_working_dir")
def test_update_working_dir_to_tree_errors(
    mock_extract_blob_to_working_dir,
    mock_get_files_from_tree,
    temp_dir: pathlib.Path,
):
    """
    Test that update_working_dir_to_tree handles errors properly.
    """

    # Setup mocks
    repo_path = temp_dir
    tree_hash = "tree123"

    # Test case 1: Exception during get_files_from_tree
    mock_get_files_from_tree.side_effect = Exception("Test error")

    # Call the function
    result = update_working_dir_to_tree(repo_path, tree_hash)

    # Assert result is False
    assert result is False

    # Test case 2: get_files_from_tree returns empty result
    mock_get_files_from_tree.side_effect = None
    mock_get_files_from_tree.return_value = {}

    # Call the function
    result = update_working_dir_to_tree(repo_path, tree_hash)

    # Assert result is False
    assert result is False

    # Test case 3: Extract blob fails
    mock_get_files_from_tree.return_value = {"file1.txt": "blob1"}
    mock_extract_blob_to_working_dir.return_value = False

    # Call the function
    result = update_working_dir_to_tree(repo_path, tree_hash)

    # Assert result is False
    assert result is False

    # Test case 4: With specific files
    mock_get_files_from_tree.reset_mock()
    mock_extract_blob_to_working_dir.reset_mock()

    mock_get_files_from_tree.return_value = {"file1.txt": "blob1", "file2.txt": "blob2"}
    mock_extract_blob_to_working_dir.return_value = True

    # Call the function with specific files
    result = update_working_dir_to_tree(repo_path, tree_hash, ["file1.txt"])

    # Assert result is True
    assert result is True

    # Verify only file1.txt was extracted
    assert mock_extract_blob_to_working_dir.call_count == 1


# Test restore_files failures
@patch("clony.internals.checkout.find_git_repo_path")
def test_restore_files_no_repo(
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that restore_files handles missing repository.
    """

    # Mock no repository found
    mock_find_git_repo_path.return_value = None

    # Call the function
    result = restore_files(["file1.txt"])

    # Assert result is False
    assert result is False


# Test restore_files with HEAD commit failure
@patch("clony.internals.checkout.find_git_repo_path")
@patch("clony.internals.checkout.get_head_commit")
def test_restore_files_no_head(
    mock_get_head_commit,
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that restore_files handles missing HEAD commit.
    """

    # Setup mocks
    repo_path = temp_dir
    mock_find_git_repo_path.return_value = repo_path

    # Mock no HEAD commit
    mock_get_head_commit.return_value = None

    # Call the function
    result = restore_files(["file1.txt"])

    # Assert result is False
    assert result is False


# Test restore_files with branch reference
@patch("clony.internals.checkout.find_git_repo_path")
@patch("clony.internals.checkout.get_ref_hash")
@patch("clony.internals.checkout.detect_conflicts")
@patch("clony.internals.checkout.restore_specific_files")
def test_restore_files_branch(
    mock_restore_specific_files,
    mock_detect_conflicts,
    mock_get_ref_hash,
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that restore_files works with a branch reference.
    """

    # Setup mocks
    repo_path = temp_dir
    mock_find_git_repo_path.return_value = repo_path

    # Mock branch reference
    branch_hash = "abcdef1234567890"
    mock_get_ref_hash.return_value = branch_hash

    # Mock no conflicts
    mock_detect_conflicts.return_value = {}

    # Mock successful restore
    mock_restore_specific_files.return_value = True

    # Call the function with a branch reference
    file_paths = ["file1.txt", "file2.txt"]
    result = restore_files(file_paths, "main")

    # Assert result is True
    assert result is True

    # Verify mock calls
    mock_get_ref_hash.assert_called_once_with(repo_path, "refs/heads/main")
    mock_detect_conflicts.assert_called_once_with(repo_path, branch_hash, file_paths)
    mock_restore_specific_files.assert_called_once_with(
        repo_path, branch_hash, file_paths
    )


# Test restore_files with invalid reference
@patch("clony.internals.checkout.find_git_repo_path")
@patch("clony.internals.checkout.get_ref_hash")
@patch("clony.internals.checkout.validate_commit_reference")
def test_restore_files_invalid_ref(
    mock_validate_commit_reference,
    mock_get_ref_hash,
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that restore_files handles invalid references.
    """

    # Setup mocks
    repo_path = temp_dir
    mock_find_git_repo_path.return_value = repo_path

    # Mock invalid branch and commit reference
    mock_get_ref_hash.return_value = None
    mock_validate_commit_reference.return_value = None

    # Call the function
    result = restore_files(["file1.txt"], "invalid-ref")

    # Assert result is False
    assert result is False


# Test restore_files with conflicts
@patch("clony.internals.checkout.find_git_repo_path")
@patch("clony.internals.checkout.get_head_commit")
@patch("clony.internals.checkout.detect_conflicts")
@patch("clony.internals.checkout.display_conflicts")
def test_restore_files_conflicts(
    mock_display_conflicts,
    mock_detect_conflicts,
    mock_get_head_commit,
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that restore_files handles conflicts.
    """

    # Setup mocks
    repo_path = temp_dir
    mock_find_git_repo_path.return_value = repo_path

    # Mock HEAD commit
    commit_hash = "abcdef1234567890"
    mock_get_head_commit.return_value = commit_hash

    # Mock conflicts
    conflicts = {"file1.txt": "modified"}
    mock_detect_conflicts.return_value = conflicts

    # Call the function
    result = restore_files(["file1.txt"])

    # Assert result is False
    assert result is False

    # Verify display_conflicts was called
    mock_display_conflicts.assert_called_once_with(conflicts)


# Test restore_files with restore failure
@patch("clony.internals.checkout.find_git_repo_path")
@patch("clony.internals.checkout.get_head_commit")
@patch("clony.internals.checkout.detect_conflicts")
@patch("clony.internals.checkout.restore_specific_files")
def test_restore_files_restore_failure(
    mock_restore_specific_files,
    mock_detect_conflicts,
    mock_get_head_commit,
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that restore_files handles restoration failure.
    """

    # Setup mocks
    repo_path = temp_dir
    mock_find_git_repo_path.return_value = repo_path

    # Mock HEAD commit
    commit_hash = "abcdef1234567890"
    mock_get_head_commit.return_value = commit_hash

    # Mock no conflicts
    mock_detect_conflicts.return_value = {}

    # Mock restore failure
    mock_restore_specific_files.return_value = False

    # Call the function
    result = restore_files(["file1.txt"])

    # Assert result is False
    assert result is False


# Test the restore_specific_files function
@patch("clony.internals.checkout.get_commit_tree_hash")
@patch("clony.internals.checkout.update_working_dir_to_tree")
def test_restore_specific_files(
    mock_update_working_dir_to_tree,
    mock_get_commit_tree_hash,
    temp_dir: pathlib.Path,
):
    """
    Test that restore_specific_files correctly restores files from a commit.
    """

    # Setup mocks
    repo_path = temp_dir
    commit_hash = "abcdef1234567890"
    file_paths = ["file1.txt", "file2.txt"]

    # Test case 1: Success
    tree_hash = "tree123"
    mock_get_commit_tree_hash.return_value = tree_hash
    mock_update_working_dir_to_tree.return_value = True

    # Call the function
    result = restore_specific_files(repo_path, commit_hash, file_paths)

    # Assert result is True
    assert result is True

    # Verify calls
    mock_get_commit_tree_hash.assert_called_once_with(repo_path, commit_hash)
    mock_update_working_dir_to_tree.assert_called_once_with(
        repo_path, tree_hash, file_paths
    )

    # Test case 2: Failed to get tree hash
    mock_get_commit_tree_hash.reset_mock()
    mock_update_working_dir_to_tree.reset_mock()

    mock_get_commit_tree_hash.return_value = None

    # Call the function
    result = restore_specific_files(repo_path, commit_hash, file_paths)

    # Assert result is False
    assert result is False

    # Verify no update was attempted
    mock_update_working_dir_to_tree.assert_not_called()


# Test switch_branch_or_commit failures
@patch("clony.internals.checkout.find_git_repo_path")
def test_switch_branch_or_commit_no_repo(
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that switch_branch_or_commit handles missing repository.
    """

    # Mock no repository found
    mock_find_git_repo_path.return_value = None

    # Call the function
    result = switch_branch_or_commit("main")

    # Assert result is False
    assert result is False


# Test switch_branch_or_commit with invalid reference
@patch("clony.internals.checkout.find_git_repo_path")
@patch("clony.internals.checkout.get_ref_hash")
@patch("clony.internals.checkout.validate_commit_reference")
def test_switch_branch_or_commit_invalid_ref(
    mock_validate_commit_reference,
    mock_get_ref_hash,
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that switch_branch_or_commit handles invalid references.
    """

    # Setup mocks
    repo_path = temp_dir
    mock_find_git_repo_path.return_value = repo_path

    # Mock invalid branch and commit reference
    mock_get_ref_hash.return_value = None
    mock_validate_commit_reference.return_value = None

    # Call the function
    result = switch_branch_or_commit("invalid-ref")

    # Assert result is False
    assert result is False


# Test switch_branch_or_commit with conflicts
@patch("clony.internals.checkout.find_git_repo_path")
@patch("clony.internals.checkout.get_ref_hash")
@patch("clony.internals.checkout.validate_commit_reference")
@patch("clony.internals.checkout.detect_conflicts")
@patch("clony.internals.checkout.display_conflicts")
def test_switch_branch_or_commit_conflicts(
    mock_display_conflicts,
    mock_detect_conflicts,
    mock_validate_commit_reference,
    mock_get_ref_hash,
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that switch_branch_or_commit handles conflicts.
    """

    # Setup mocks
    repo_path = temp_dir
    mock_find_git_repo_path.return_value = repo_path

    # Mock commit reference
    commit_hash = "abcdef1234567890"
    mock_get_ref_hash.return_value = None
    mock_validate_commit_reference.return_value = commit_hash

    # Mock conflicts
    conflicts = {"file1.txt": "modified"}
    mock_detect_conflicts.return_value = conflicts

    # Call the function
    result = switch_branch_or_commit("commit-ref")

    # Assert result is False
    assert result is False

    # Verify display_conflicts was called
    mock_display_conflicts.assert_called_once_with(conflicts)

    # Test with force option
    mock_detect_conflicts.reset_mock()
    mock_display_conflicts.reset_mock()

    # Call the function with force=True
    result = switch_branch_or_commit("commit-ref", force=True)

    # Verify detect_conflicts was not called
    mock_detect_conflicts.assert_not_called()


# Test switch_branch_or_commit with commit (detached HEAD)
@patch("clony.internals.checkout.find_git_repo_path")
@patch("clony.internals.checkout.get_ref_hash")
@patch("clony.internals.checkout.validate_commit_reference")
@patch("clony.internals.checkout.detect_conflicts")
@patch("clony.internals.checkout.get_commit_tree_hash")
@patch("clony.internals.checkout.get_files_from_tree")
@patch("clony.internals.checkout.update_head_to_commit")
@patch("clony.internals.checkout.update_index_to_commit")
@patch("clony.internals.checkout.update_working_dir_to_tree")
@patch("clony.internals.checkout.display_checkout_info")
def test_switch_branch_or_commit_detached(
    mock_display_checkout_info,
    mock_update_working_dir_to_tree,
    mock_update_index_to_commit,
    mock_update_head_to_commit,
    mock_get_files_from_tree,
    mock_get_commit_tree_hash,
    mock_detect_conflicts,
    mock_validate_commit_reference,
    mock_get_ref_hash,
    mock_find_git_repo_path,
    temp_dir: pathlib.Path,
):
    """
    Test that switch_branch_or_commit switches to a commit correctly.
    """

    # Setup mocks
    repo_path = temp_dir
    mock_find_git_repo_path.return_value = repo_path

    # Mock commit reference
    commit_hash = "abcdef1234567890"
    mock_get_ref_hash.return_value = None
    mock_validate_commit_reference.return_value = commit_hash

    # Mock no conflicts
    mock_detect_conflicts.return_value = {}

    # Mock tree hash
    tree_hash = "tree123"
    mock_get_commit_tree_hash.return_value = tree_hash

    # Mock file list
    mock_get_files_from_tree.return_value = {"file1.txt": "blob1", "file2.txt": "blob2"}

    # Mock successful updates
    mock_update_head_to_commit.return_value = True
    mock_update_index_to_commit.return_value = True
    mock_update_working_dir_to_tree.return_value = True

    # Call the function
    result = switch_branch_or_commit("commit-ref")

    # Assert result is True
    assert result is True

    # Verify mock calls
    mock_update_head_to_commit.assert_called_once_with(repo_path, commit_hash)
    mock_update_index_to_commit.assert_called_once_with(repo_path, commit_hash)
    mock_update_working_dir_to_tree.assert_called_once_with(repo_path, tree_hash)
    mock_display_checkout_info.assert_called_once_with("commit-ref", False, True, 2)

    # Test failures
    # 1. get_commit_tree_hash failure
    mock_get_commit_tree_hash.return_value = None

    # Call the function
    result = switch_branch_or_commit("commit-ref")

    # Assert result is False
    assert result is False

    # 2. update_head_to_commit failure
    mock_get_commit_tree_hash.return_value = tree_hash
    mock_update_head_to_commit.return_value = False

    # Call the function
    result = switch_branch_or_commit("commit-ref")

    # Assert result is False
    assert result is False

    # 3. update_index_to_commit failure
    mock_update_head_to_commit.return_value = True
    mock_update_index_to_commit.return_value = False

    # Call the function
    result = switch_branch_or_commit("commit-ref")

    # Assert result is False
    assert result is False

    # 4. update_working_dir_to_tree failure
    mock_update_index_to_commit.return_value = True
    mock_update_working_dir_to_tree.return_value = False

    # Call the function
    result = switch_branch_or_commit("commit-ref")

    # Assert result is False
    assert result is False


# Test display_checkout_info
@patch("clony.internals.checkout.console.print")
def test_display_checkout_info(
    mock_print,
    temp_dir: pathlib.Path,
):
    """
    Test that display_checkout_info formats output correctly.
    """

    # Call the function for a branch
    display_checkout_info("main", True, False, 10)

    # Verify console.print was called
    assert mock_print.call_count == 1

    # Call the function for a detached HEAD
    mock_print.reset_mock()
    display_checkout_info("abcdef12", False, True, 5)

    # Verify console.print was called twice (once for table, once for warning)
    assert mock_print.call_count == 2


# Test display_conflicts
@patch("clony.internals.checkout.console.print")
def test_display_conflicts(
    mock_print,
    temp_dir: pathlib.Path,
):
    """
    Test that display_conflicts formats output correctly.
    """

    # Setup conflicts
    conflicts = {"file1.txt": "modified", "file2.txt": "deleted"}

    # Call the function
    display_conflicts(conflicts)

    # Verify console.print was called twice (once for table, once for help panel)
    assert mock_print.call_count == 2


# Test specific file filtering in detect_conflicts
@patch("clony.internals.checkout.get_repository_status")
@patch("clony.internals.checkout.get_commit_tree_hash")
@patch("clony.internals.checkout.get_files_from_tree")
def test_detect_conflicts_with_specific_files(
    mock_get_files_from_tree,
    mock_get_commit_tree_hash,
    mock_get_repository_status,
    temp_dir: pathlib.Path,
):
    """
    Test that detect_conflicts correctly filters specific files.
    """

    # Setup mocks
    repo_path = temp_dir
    commit_hash = "commit123"

    # Mock status
    status_dict = {
        FileStatus.MODIFIED: ["file1.txt", "file2.txt"],
        FileStatus.BOTH_MODIFIED: ["file3.txt"],
        FileStatus.DELETED: ["file4.txt"],
        FileStatus.BOTH_DELETED: ["file5.txt"],
    }
    mock_get_repository_status.return_value = status_dict

    # Mock tree hash
    tree_hash = "tree123"
    mock_get_commit_tree_hash.return_value = tree_hash

    # Mock target files
    mock_get_files_from_tree.return_value = {
        "file1.txt": "blob1",
        "file3.txt": "blob3",
        "file4.txt": "blob4",
        "file5.txt": "blob5",
    }

    # Call the function with specific files filter
    result = detect_conflicts(repo_path, commit_hash, ["file1.txt", "file5.txt"])

    # Assert result
    assert "file1.txt" in result  # Should be included as it's modified and in filter
    assert "file3.txt" not in result  # Should be excluded as it's not in filter
    assert "file5.txt" in result  # Should be included as it's deleted and in filter

    # Verify get_repository_status was called once
    mock_get_repository_status.assert_called_once_with(str(repo_path))


# Test get_commit_tree_hash with no tree line in commit
@patch("clony.internals.checkout.read_git_object")
def test_get_commit_tree_hash_no_tree_line(
    mock_read_git_object,
    temp_dir: pathlib.Path,
):
    """
    Test that get_commit_tree_hash handles commit without tree line.
    """

    # Setup mock
    repo_path = temp_dir
    commit_hash = "commit123"

    # Mock commit content without tree line
    mock_read_git_object.return_value = (
        "commit",
        b"author Some Author\ncommitter Some Committer",
    )

    # Call the function
    result = get_commit_tree_hash(repo_path, commit_hash)

    # Assert result is None
    assert result is None


# Test target tree hash not found in detect_conflicts
@patch("clony.internals.checkout.get_repository_status")
@patch("clony.internals.checkout.get_commit_tree_hash")
def test_detect_conflicts_no_tree_hash(
    mock_get_commit_tree_hash,
    mock_get_repository_status,
    temp_dir: pathlib.Path,
):
    """
    Test that detect_conflicts handles missing tree hash gracefully.
    """

    # Setup mocks
    repo_path = temp_dir
    commit_hash = "commit123"

    # Mock status
    status_dict = {
        FileStatus.MODIFIED: ["file1.txt"],
    }
    mock_get_repository_status.return_value = status_dict

    # Mock tree hash not found
    mock_get_commit_tree_hash.return_value = None

    # Call the function
    result = detect_conflicts(repo_path, commit_hash)

    # Assert result is empty
    assert result == {}


# Test restore_files with force flag
@pytest.mark.unit
def test_restore_files_with_force(temp_dir: pathlib.Path):
    """Test restore_files with force flag."""

    # Setup mocks
    repo_path = temp_dir
    paths = ["file1.txt", "file2.txt"]
    source_ref = "HEAD"
    force = True

    # Mock
    with patch("clony.internals.checkout.find_git_repo_path", return_value=repo_path):
        with patch(
            "clony.internals.checkout.get_head_commit", return_value="commit123"
        ):
            with patch(
                "clony.internals.checkout.detect_conflicts"
            ) as mock_detect_conflicts:
                with patch(
                    "clony.internals.checkout.restore_specific_files", return_value=True
                ) as mock_restore:
                    with patch("clony.internals.checkout.console.print"):
                        # Execute
                        result = restore_files(paths, source_ref, force=force)

                        # Verify
                        assert result is True
                        mock_restore.assert_called_once_with(
                            repo_path, "commit123", paths
                        )
                        # Verify that detect_conflicts was not called due to force flag
                        mock_detect_conflicts.assert_not_called()
