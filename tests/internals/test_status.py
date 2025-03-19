"""
Tests for the status module.

This module contains tests for the status functions.
"""

# Standard library imports
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest

# Local imports
from clony.internals.status import (
    FileStatus,
    display_status_info,
    format_status_output,
    get_all_files,
    get_commit_tree,
    get_file_content_hash,
    get_file_status,
    get_repository_status,
    get_staged_files,
    get_status,
    get_tracked_files,
)


# Test for the FileStatus enum
@pytest.mark.unit
def test_file_status_enum():
    """
    Test that the FileStatus enum has all the required statuses.
    """

    # Check that the enum has all the required statuses
    assert hasattr(FileStatus, "UNMODIFIED")
    assert hasattr(FileStatus, "MODIFIED")
    assert hasattr(FileStatus, "STAGED_NEW")
    assert hasattr(FileStatus, "STAGED_MODIFIED")
    assert hasattr(FileStatus, "STAGED_DELETED")
    assert hasattr(FileStatus, "UNTRACKED")
    assert hasattr(FileStatus, "DELETED")
    assert hasattr(FileStatus, "BOTH_MODIFIED")
    assert hasattr(FileStatus, "BOTH_DELETED")


# Test for get_file_content_hash function
@pytest.mark.unit
def test_get_file_content_hash():
    """
    Test calculating the hash of a file's content.
    """

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        # Write test content to the file
        temp_file.write(b"test content")

        # Get the path to the temporary file
        temp_path = Path(temp_file.name)

    try:
        # Test with existing file
        hash_value = get_file_content_hash(temp_path)
        assert hash_value == "1eebdf4fdc9fc7bf283031b93f9aef3338de9052"

        # Test with non-existent file
        non_existent_path = Path("non_existent_file.txt")
        hash_value = get_file_content_hash(non_existent_path)
        assert hash_value == ""

    finally:
        # Clean up
        os.unlink(temp_path)


# Test for get_file_status function
@pytest.mark.unit
def test_get_file_status():
    """
    Test detecting untracked files.
    """

    # Define the file path, repository path, tracked files,
    # staged files, and working directory files
    file_path = "test.txt"
    repo_path = Path("/repo")
    tracked_files = {}
    staged_files = {}
    working_dir_files = {"test.txt"}

    # Get the status of the file
    status = get_file_status(
        file_path, repo_path, tracked_files, staged_files, working_dir_files
    )

    # Check that the status is UNTRACKED
    assert status == FileStatus.UNTRACKED


# Test for get_file_status function
@pytest.mark.unit
def test_get_file_status_deleted():
    """
    Test detecting deleted files.
    """

    # Define the file path, repository path, tracked files,
    # staged files, and working directory files
    file_path = "test.txt"
    repo_path = Path("/repo")
    tracked_files = {"test.txt": "hash1"}
    staged_files = {}
    working_dir_files = set()

    # Get the status of the file
    status = get_file_status(
        file_path, repo_path, tracked_files, staged_files, working_dir_files
    )

    # Check that the status is DELETED
    assert status == FileStatus.DELETED


# Test for get_file_status function
@pytest.mark.unit
def test_get_file_status_staged_new():
    """
    Test detecting newly staged files.
    """

    # Define the file path, repository path, tracked files,
    # staged files, and working directory files
    file_path = "test.txt"
    repo_path = Path("/repo")
    tracked_files = {}
    staged_files = {"test.txt": "hash1"}
    working_dir_files = {"test.txt"}

    # Mock get_file_content_hash to return the same hash as in staged_files
    with patch("clony.internals.status.get_file_content_hash", return_value="hash1"):
        # Get the status of the file
        status = get_file_status(
            file_path, repo_path, tracked_files, staged_files, working_dir_files
        )

        # Check that the status is STAGED_NEW
        assert status == FileStatus.STAGED_NEW


# Test for get_file_status function
@pytest.mark.unit
def test_get_file_status_both_modified():
    """
    Test detecting files that are staged but then modified again.
    """

    # Define the file path, repository path, tracked files,
    # staged files, and working directory files
    file_path = "test.txt"
    repo_path = Path("/repo")
    tracked_files = {}
    staged_files = {"test.txt": "hash1"}
    working_dir_files = {"test.txt"}

    # Mock get_file_content_hash to return a different hash than in staged_files
    with patch("clony.internals.status.get_file_content_hash", return_value="hash2"):
        # Get the status of the file
        status = get_file_status(
            file_path, repo_path, tracked_files, staged_files, working_dir_files
        )

        # Check that the status is BOTH_MODIFIED
        assert status == FileStatus.BOTH_MODIFIED


# Test for get_file_status function
@pytest.mark.unit
def test_get_file_status_staged_deleted():
    """
    Test detecting files that are staged for deletion.
    """

    # Define the file path, repository path, tracked files,
    # staged files, and working directory files
    file_path = "test.txt"
    repo_path = Path("/repo")
    tracked_files = {"test.txt": "hash1"}
    staged_files = {"test.txt": "hash1"}
    working_dir_files = set()

    # Get the status of the file
    status = get_file_status(
        file_path, repo_path, tracked_files, staged_files, working_dir_files
    )

    # Check that the status is STAGED_DELETED
    assert status == FileStatus.STAGED_DELETED


# Test for get_file_status function
@pytest.mark.unit
def test_get_file_status_both_deleted():
    """
    Test detecting files that are staged but then deleted.
    """

    # Define the file path, repository path, tracked files,
    # staged files, and working directory files
    file_path = "test.txt"
    repo_path = Path("/repo")
    tracked_files = {}
    staged_files = {"test.txt": "hash1"}
    working_dir_files = set()

    # Get the status of the file
    status = get_file_status(
        file_path, repo_path, tracked_files, staged_files, working_dir_files
    )

    # Check that the status is BOTH_DELETED
    assert status == FileStatus.BOTH_DELETED


# Test for get_file_status function
@pytest.mark.unit
def test_get_file_status_modified():
    """
    Test detecting modified files.
    """

    # Define the file path, repository path, tracked files,
    # staged files, and working directory files
    file_path = "test.txt"
    repo_path = Path("/repo")
    tracked_files = {"test.txt": "hash1"}
    staged_files = {}
    working_dir_files = {"test.txt"}

    # Mock get_file_content_hash to return a different hash than in tracked_files
    with patch("clony.internals.status.get_file_content_hash", return_value="hash2"):
        # Get the status of the file
        status = get_file_status(
            file_path, repo_path, tracked_files, staged_files, working_dir_files
        )

        # Check that the status is MODIFIED
        assert status == FileStatus.MODIFIED


# Test for get_file_status function
@pytest.mark.unit
def test_get_file_status_staged_modified():
    """
    Test detecting files that are staged with modifications.
    """

    # Define the file path, repository path, tracked files,
    # staged files, and working directory files
    file_path = "test.txt"
    repo_path = Path("/repo")
    tracked_files = {"test.txt": "hash1"}
    staged_files = {"test.txt": "hash2"}
    working_dir_files = {"test.txt"}

    # Mock get_file_content_hash to return the same hash as in staged_files
    with patch("clony.internals.status.get_file_content_hash", return_value="hash2"):
        # Get the status of the file
        status = get_file_status(
            file_path, repo_path, tracked_files, staged_files, working_dir_files
        )

        # Check that the status is STAGED_MODIFIED
        assert status == FileStatus.STAGED_MODIFIED


# Test for get_file_status function
@pytest.mark.unit
def test_get_file_status_unmodified():
    """
    Test detecting unmodified files.
    """

    # Define the file path, repository path, tracked files,
    # staged files, and working directory files
    file_path = "test.txt"
    repo_path = Path("/repo")
    tracked_files = {"test.txt": "hash1"}
    staged_files = {}
    working_dir_files = {"test.txt"}

    # Mock get_file_content_hash to return the same hash as in tracked_files
    with patch("clony.internals.status.get_file_content_hash", return_value="hash1"):
        # Get the status of the file
        status = get_file_status(
            file_path, repo_path, tracked_files, staged_files, working_dir_files
        )

        # Check that the status is UNMODIFIED
        assert status == FileStatus.UNMODIFIED


# Test for format_status_output function
@pytest.mark.unit
def test_format_status_output():
    """
    Test formatting the status output.
    """

    # Define the status dictionary
    status_dict = {
        FileStatus.UNMODIFIED: [],
        FileStatus.MODIFIED: ["modified.txt"],
        FileStatus.STAGED_NEW: ["new.txt"],
        FileStatus.STAGED_MODIFIED: ["staged_modified.txt"],
        FileStatus.STAGED_DELETED: ["staged_deleted.txt"],
        FileStatus.UNTRACKED: ["untracked.txt"],
        FileStatus.DELETED: ["deleted.txt"],
        FileStatus.BOTH_MODIFIED: ["both_modified.txt"],
        FileStatus.BOTH_DELETED: ["both_deleted.txt"],
    }

    # Format the status output
    output = format_status_output(status_dict)

    # Check that the output contains all the expected sections and files
    assert "Changes to be committed:" in output
    assert "new file:   new.txt" in output
    assert "modified:   staged_modified.txt" in output
    assert "deleted:    staged_deleted.txt" in output

    assert "Changes not staged for commit:" in output
    assert "modified:   modified.txt" in output
    assert "deleted:    deleted.txt" in output
    assert "modified:   both_modified.txt" in output
    assert "deleted:    both_deleted.txt" in output

    assert "Untracked files:" in output
    assert "untracked.txt" in output


# Test for get_repository_status function
@pytest.mark.unit
def test_get_repository_status():
    """
    Test getting the status of all files in the repository.
    """

    # Mock the necessary functions
    with (
        patch("clony.internals.status.find_git_repo_path", return_value=Path("/repo")),
        patch(
            "clony.internals.status.get_tracked_files",
            return_value={"tracked.txt": "hash1"},
        ),
        patch(
            "clony.internals.status.get_staged_files",
            return_value={"staged.txt": "hash2"},
        ),
        patch("clony.internals.status.get_all_files", return_value={"working.txt"}),
        patch(
            "clony.internals.status.get_file_status", return_value=FileStatus.UNMODIFIED
        ),
    ):

        # Get the status of the repository
        status_dict = get_repository_status("/repo")

        # Check that get_file_status was called for each file
        assert len(status_dict[FileStatus.UNMODIFIED]) == 3


# Test for get_status function
@pytest.mark.unit
def test_get_status():
    """
    Test the main get_status function.
    """

    # Define the status dictionary
    status_dict = {status: [] for status in FileStatus}
    status_dict[FileStatus.MODIFIED] = ["modified.txt"]

    # Mock the necessary functions
    with (
        patch("clony.internals.status.get_repository_status", return_value=status_dict),
        patch(
            "clony.internals.status.format_status_output",
            return_value="Formatted output",
        ),
    ):

        # Get the status of the repository
        result_dict, formatted_output = get_status(".")

        # Check that the result contains the expected values
        assert result_dict == status_dict
        assert formatted_output == "Formatted output"


# Test for get_commit_tree function
@pytest.mark.unit
def test_get_commit_tree():
    """
    Test getting the file tree from a commit.
    """

    # Define the repository path
    repo_path = Path("/repo")

    # Test with empty commit hash
    result = get_commit_tree(repo_path, "")
    assert result == {}

    # Test with non-existent commit file
    with patch("pathlib.Path.exists", return_value=False):
        result = get_commit_tree(repo_path, "abcdef")
        assert result == {}

    # Test with existing HEAD_TREE file
    with (
        patch("pathlib.Path.exists", side_effect=[True, True]),
        patch(
            "clony.internals.status.read_index_file", return_value={"file.txt": "hash1"}
        ),
    ):
        result = get_commit_tree(repo_path, "abcdef")
        assert result == {"file.txt": "hash1"}

    # Test with exception
    with (
        patch("pathlib.Path.exists", side_effect=[True, True]),
        patch(
            "clony.internals.status.read_index_file",
            side_effect=Exception("Test error"),
        ),
    ):
        result = get_commit_tree(repo_path, "abcdef")
        assert result == {}


# Test for get_tracked_files function
@pytest.mark.unit
def test_get_tracked_files():
    """
    Test getting all tracked files from the last commit.
    """

    # Define the repository path
    repo_path = Path("/repo")

    # Test with get_head_commit returning a commit hash
    with (
        patch("clony.internals.status.get_head_commit", return_value="abcdef"),
        patch(
            "clony.internals.status.get_commit_tree", return_value={"file.txt": "hash1"}
        ),
    ):
        result = get_tracked_files(repo_path)
        assert result == {"file.txt": "hash1"}


# Test for get_staged_files function
@pytest.mark.unit
def test_get_staged_files():
    """
    Test getting all staged files from the index.
    """

    # Define the repository path
    repo_path = Path("/repo")

    # Test with read_index_file returning staged files
    with patch(
        "clony.internals.status.read_index_file", return_value={"file.txt": "hash1"}
    ):
        result = get_staged_files(repo_path)
        assert result == {"file.txt": "hash1"}


# Test for get_all_files function
@pytest.mark.unit
def test_get_all_files():
    """
    Test getting all files in the repository.
    """

    # Define the repository path
    repo_path = Path("/repo")

    # Mock os.walk to return some files
    mock_walk_data = [
        ("/repo", ["dir1", ".git"], ["file1.txt"]),
        ("/repo/dir1", [], ["file2.txt"]),
        ("/repo/.git", [], ["HEAD"]),
    ]

    # Mock the os.walk function
    with (
        patch("os.walk", return_value=mock_walk_data),
        patch("pathlib.Path.relative_to", side_effect=["file1.txt", "dir1/file2.txt"]),
    ):
        result = get_all_files(repo_path)
        assert "file1.txt" in result
        assert "dir1/file2.txt" in result
        assert len(result) == 2


# Test for get_repository_status function
@pytest.mark.unit
def test_get_repository_status_not_git_repo():
    """
    Test get_repository_status with a non-git repository.
    """

    # Mock the find_git_repo_path function
    with patch("clony.internals.status.find_git_repo_path", return_value=None):
        result = get_repository_status("/not-a-repo")
        assert result == {}


# Test for get_repository_status function
@pytest.mark.unit
def test_get_repository_status_exception():
    """
    Test get_repository_status with an exception.
    """

    # Mock the find_git_repo_path function
    with patch(
        "clony.internals.status.find_git_repo_path", side_effect=Exception("Test error")
    ):
        result = get_repository_status("/repo")
        assert result == {}


# Test for format_status_output function
@pytest.mark.unit
def test_format_status_output_empty():
    """
    Test formatting the status output with empty status.
    """

    # Define the status dictionary
    status_dict = {status: [] for status in FileStatus}

    # Format the status output
    output = format_status_output(status_dict)

    # Check that the output contains the expected message
    assert "nothing to commit, working tree clean" in output


# Test for get_commit_tree function
@pytest.mark.unit
def test_get_commit_tree_with_error_handling():
    """
    Test error handling in get_commit_tree function.
    """

    # Define the repository path
    repo_path = Path("/repo")
    commit_hash = "abcdef"

    # Test with commit file not existing
    with patch("pathlib.Path.exists", side_effect=[True, False]):
        result = get_commit_tree(repo_path, commit_hash)
        assert result == {}


# Test for get_file_content_hash function
@pytest.mark.unit
def test_get_file_content_hash_with_error():
    """
    Test error handling in get_file_content_hash function.
    """

    # Define the file path
    file_path = Path("/repo/file.txt")

    # Test with file opening raising an exception
    with patch("builtins.open", side_effect=Exception("Test error")):
        # Just verify that the function returns an empty string on error
        result = get_file_content_hash(file_path)
        assert result == ""


# Test for get_file_status function
@pytest.mark.unit
def test_get_file_status_edge_cases():
    """
    Test edge cases in get_file_status function.
    """

    # Define the file path
    file_path = "test.txt"
    repo_path = Path("/repo")

    # Test with file that is tracked, staged, and exists (but with different hashes)
    tracked_files = {"test.txt": "hash1"}
    staged_files = {"test.txt": "hash2"}
    working_dir_files = {"test.txt"}

    # Mock get_file_content_hash to return a hash different from both tracked and staged
    with patch("clony.internals.status.get_file_content_hash", return_value="hash3"):
        status = get_file_status(
            file_path, repo_path, tracked_files, staged_files, working_dir_files
        )
        assert status == FileStatus.BOTH_MODIFIED


# Test for get_commit_tree function
@pytest.mark.unit
def test_get_commit_tree_with_head_tree():
    """
    Test get_commit_tree with HEAD_TREE file.
    """

    # Define the repository path
    repo_path = Path("/repo")
    commit_hash = "abcdef"

    # Test with HEAD_TREE file existing and readable
    with (
        patch("pathlib.Path.exists", side_effect=[True, True, True]),
        patch(
            "clony.internals.status.read_index_file", return_value={"file.txt": "hash1"}
        ),
    ):
        result = get_commit_tree(repo_path, commit_hash)
        assert result == {"file.txt": "hash1"}


# Test for get_file_content_hash function
@pytest.mark.unit
def test_get_file_content_hash_exception_path():
    """
    Test the exception path in get_file_content_hash.
    """

    # Create a Path object that will raise an exception when accessed
    file_path = MagicMock(spec=Path)
    file_path.exists.return_value = True
    file_path.is_file.return_value = True
    file_path.__str__.return_value = "/repo/file.txt"

    # Make open raise an exception
    with patch("builtins.open", side_effect=Exception("Test error")):
        # Call the function
        result = get_file_content_hash(file_path)

        # Verify the result
        assert result == ""


# Test for get_commit_tree function
@pytest.mark.unit
def test_get_commit_tree_with_head_tree_error():
    """
    Test get_commit_tree with HEAD_TREE file that raises an error when read.
    """

    # Define the repository path
    repo_path = Path("/repo")
    commit_hash = "abcdef"

    # Test with HEAD_TREE file existing but raising an error when read
    with (
        patch("pathlib.Path.exists", side_effect=[True, True]),
        patch(
            "clony.internals.status.read_index_file",
            side_effect=Exception("Test error"),
        ),
        patch("clony.internals.status.logger.error") as mock_logger,
    ):
        result = get_commit_tree(repo_path, commit_hash)
        assert result == {}
        # Verify that the error was logged
        mock_logger.assert_called_with("Error reading HEAD_TREE file: Test error")


# Test for get_commit_tree function
@pytest.mark.unit
def test_get_commit_tree_exception_handling():
    """
    Test exception handling in the get_commit_tree function.
    """

    # Define the commit hash
    commit_hash = "abcdef"

    # Create a mock path that will raise an exception when accessed
    mock_path = MagicMock(spec=Path)
    mock_path.__truediv__.side_effect = Exception("Test error")

    # Mock the logger
    with patch("clony.internals.status.logger.error") as mock_logger:
        # Call the function with our mocked path
        result = get_commit_tree(mock_path, commit_hash)

        # Verify the result and that the error was logged
        assert result == {}
        mock_logger.assert_called_with("Error reading commit tree: Test error")


# Test for format_status_output function with COLOR_SUPPORT
@pytest.mark.unit
def test_format_status_output_with_color():
    """
    Test formatting the status output with color support.
    """

    # Define the status dictionary with values in each category
    status_dict = {status: [] for status in FileStatus}
    status_dict[FileStatus.STAGED_NEW] = ["staged_new.txt"]
    status_dict[FileStatus.MODIFIED] = ["modified.txt"]
    status_dict[FileStatus.UNTRACKED] = ["untracked.txt"]

    # Test with COLOR_SUPPORT set to True
    with (
        patch("clony.internals.status.COLOR_SUPPORT", True),
        patch("clony.internals.status.Fore.GREEN", "GREEN"),
        patch("clony.internals.status.Fore.RED", "RED"),
        patch("clony.internals.status.Fore.YELLOW", "YELLOW"),
        patch("clony.internals.status.Fore.BLUE", "BLUE"),
        patch("clony.internals.status.Style.RESET_ALL", "RESET"),
    ):

        # Format the status output
        output = format_status_output(status_dict)

        # Check that the output contains the expected color codes
        assert "GREENChanges to be committed:RESET" in output
        assert "BLUEclony reset HEAD <file>...RESET" in output
        assert "GREENnew file:   staged_new.txtRESET" in output
        assert "YELLOWChanges not staged for commit:RESET" in output
        assert "BLUEclony stage <file>...RESET" in output
        assert "YELLOWmodified:   modified.txtRESET" in output
        assert "REDUntracked files:RESET" in output
        assert "REDuntracked.txtRESET" in output

        # Test with empty status_dict (nothing to commit)
        empty_status_dict = {status: [] for status in FileStatus}
        empty_output = format_status_output(empty_status_dict)
        assert "GREENnothing to commit, working tree cleanRESET" in empty_output

    # Test with COLOR_SUPPORT set to False
    with patch("clony.internals.status.COLOR_SUPPORT", False):
        # Format the status output
        output = format_status_output(status_dict)

        # Check that the output does not contain color codes
        assert "Changes to be committed:" in output
        assert "clony reset HEAD <file>" in output
        assert "new file:   staged_new.txt" in output
        assert "Changes not staged for commit:" in output
        assert "clony stage <file>" in output
        assert "modified:   modified.txt" in output
        assert "Untracked files:" in output
        assert "untracked.txt" in output


# Test for format_status_output function with nothing to commit (for code coverage)
@pytest.mark.unit
def test_format_status_output_nothing_to_commit():
    """
    Test formatting the status output with nothing to commit and color support.
    """
    # Define an empty status dictionary
    status_dict = {status: [] for status in FileStatus}

    # Test with COLOR_SUPPORT = True
    with (
        patch("clony.internals.status.COLOR_SUPPORT", True),
        patch("clony.internals.status.Fore.GREEN", "GREEN"),
        patch("clony.internals.status.Style.RESET_ALL", "RESET"),
    ):

        # Get the output
        output = format_status_output(status_dict)

        # Check the output
        assert output == "GREENnothing to commit, working tree cleanRESET"


# Test for the display_status_info function
@pytest.mark.unit
def test_display_status_info():
    """
    Test the display_status_info function.

    This test verifies that the display_status_info function correctly creates
    and displays tables for different types of file statuses.
    """
    # Create a mock status dictionary
    status_dict = {status: [] for status in FileStatus}

    # Add some test files to different statuses
    status_dict[FileStatus.STAGED_NEW] = ["new_file.txt"]
    status_dict[FileStatus.STAGED_MODIFIED] = ["modified_staged.txt"]
    status_dict[FileStatus.MODIFIED] = ["modified_unstaged.txt"]
    status_dict[FileStatus.UNTRACKED] = ["untracked.txt"]

    # Mock the console.print method and logger.info method
    with (
        patch("clony.internals.status.console.print") as mock_console_print,
        patch("clony.internals.status.logger.info") as mock_logger_info,
    ):
        # Call the display_status_info function
        display_status_info(status_dict)

        # Verify that console.print was called for the tables
        assert mock_console_print.call_count > 0

        # Verify that logger.info was called for the helper messages
        assert mock_logger_info.call_count > 0

        # Get all the arguments passed to console.print
        call_args_list = [
            call[0][0] for call in mock_console_print.call_args_list if call[0]
        ]

        # Check if tables were created for each category
        tables = [arg for arg in call_args_list if hasattr(arg, "title")]
        table_titles = [table.title for table in tables if hasattr(table, "title")]

        # Verify that tables with appropriate titles were created
        assert "Changes to be committed" in table_titles
        assert "Untracked files" in table_titles

        # Verify the helper messages were logged
        assert any(
            "reset HEAD" in msg
            for msg in [call[0][0] for call in mock_logger_info.call_args_list]
        )
        assert any(
            "stage" in msg
            for msg in [call[0][0] for call in mock_logger_info.call_args_list]
        )


# Test for display_status_info with clean working tree
@pytest.mark.unit
def test_display_status_info_clean():
    """
    Test the display_status_info function with a clean working tree.

    This test verifies that the display_status_info function correctly displays
    a message about a clean working tree when there are no changes.
    """
    # Create an empty status dictionary (clean working tree)
    status_dict = {status: [] for status in FileStatus}

    # Mock the console.print method
    with patch("clony.internals.status.console.print") as mock_console_print:
        # Call the display_status_info function
        display_status_info(status_dict)

        # Verify that console.print was called once
        assert mock_console_print.call_count == 1

        # Get the argument passed to console.print
        table = mock_console_print.call_args[0][0]

        # Verify that the table has the correct title
        assert table.title == "Repository Status"


# Test for the display_status_info function with all file status types
@pytest.mark.unit
def test_display_status_info_all_statuses():
    """
    Test the display_status_info function with all file status types.

    This test verifies that the display_status_info function correctly handles
    and displays tables for all possible file status categories.
    """
    # Create a status dictionary with entries for all status types
    status_dict = {status: [] for status in FileStatus}

    # Add test files for each status type
    status_dict[FileStatus.STAGED_NEW] = ["staged_new.txt"]
    status_dict[FileStatus.STAGED_MODIFIED] = ["staged_modified.txt"]
    status_dict[FileStatus.STAGED_DELETED] = ["staged_deleted.txt"]
    status_dict[FileStatus.MODIFIED] = ["modified.txt"]
    status_dict[FileStatus.DELETED] = ["deleted.txt"]
    status_dict[FileStatus.BOTH_MODIFIED] = ["both_modified.txt"]
    status_dict[FileStatus.BOTH_DELETED] = ["both_deleted.txt"]
    status_dict[FileStatus.UNTRACKED] = ["untracked.txt"]

    # Mock the console.print method and logger.info method
    with (
        patch("clony.internals.status.console.print") as mock_console_print,
        patch("clony.internals.status.logger.info") as mock_logger_info,
    ):
        # Call the display_status_info function
        display_status_info(status_dict)

        # Verify that console.print was called multiple times for tables
        assert mock_console_print.call_count > 0

        # Verify that logger.info was called for helper messages
        assert mock_logger_info.call_count > 0

        # Get all the tables passed to console.print
        call_args_list = [
            call[0][0] for call in mock_console_print.call_args_list if call[0]
        ]
        tables = [arg for arg in call_args_list if hasattr(arg, "title")]

        # Verify that at least three tables were created (staged, unstaged, untracked)
        assert len(tables) >= 3


# Test for display_status_info function with exception
@pytest.mark.unit
def test_display_status_info_exception():
    """
    Test the exception handling in the display_status_info function.

    This test verifies that the display_status_info function properly catches
    and logs exceptions that occur during execution.
    """
    # Create a valid status dictionary for the initial check
    status_dict = {status: [] for status in FileStatus}

    # Add some test files to trigger unstaged files section
    status_dict[FileStatus.MODIFIED] = ["modified.txt"]

    # Mock the console.print method to raise an exception
    with patch(
        "clony.internals.status.console.print", side_effect=Exception("Test error")
    ):
        # Mock the logger.error function
        with patch("clony.internals.status.logger.error") as mock_logger:
            # Call the function, which should catch the exception
            display_status_info(status_dict)

            # Verify that logger.error was called with the correct error message
            mock_logger.assert_called_once_with("Error displaying status: Test error")
