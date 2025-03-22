"""
Tests for the CLI branch management commands.

This module contains tests for the Clony CLI branch management command:
branch (with various flags for creation, deletion, and listing).
"""

# Standard imports
import pathlib
import shutil
import tempfile
from typing import Generator
from unittest.mock import patch

# Third-party imports
import pytest
from click.testing import CliRunner

# Local imports
from clony.cli import cli


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


# Test for the branch command
@pytest.mark.cli
def test_branch_command(temp_dir: pathlib.Path):
    """
    Test the branch command functionality.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Initialize a repository
        result = runner.invoke(cli, ["init", str(temp_dir)])
        assert result.exit_code == 0

        # Create a commit hash in the main branch
        commit_hash = "1234567890abcdef1234567890abcdef12345678"
        branch_path = temp_dir / ".git" / "refs" / "heads" / "main"
        branch_path.parent.mkdir(parents=True, exist_ok=True)
        with open(branch_path, "w") as f:
            f.write(commit_hash)

        # Create a new branch
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(cli, ["branch", "test-branch"])
            assert result.exit_code == 0
            assert "Created branch 'test-branch'" in result.output

        # Verify the branch was created
        new_branch_path = temp_dir / ".git" / "refs" / "heads" / "test-branch"
        assert new_branch_path.exists()
        with open(new_branch_path, "r") as f:
            assert f.read().strip() == commit_hash


# Test for the branch command with a specific commit
@pytest.mark.cli
def test_branch_command_with_commit(temp_dir: pathlib.Path):
    """
    Test the branch command with a specific commit.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Initialize a repository
        result = runner.invoke(cli, ["init", str(temp_dir)])
        assert result.exit_code == 0

        # Create a commit hash in the main branch
        commit_hash = "1234567890abcdef1234567890abcdef12345678"
        branch_path = temp_dir / ".git" / "refs" / "heads" / "main"
        branch_path.parent.mkdir(parents=True, exist_ok=True)
        with open(branch_path, "w") as f:
            f.write(commit_hash)

        # Create a new commit hash
        new_commit = "9876543210abcdef9876543210abcdef98765432"

        # Create a new branch with the new commit
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(
                cli, ["branch", "test-branch", "--commit", new_commit]
            )
            assert result.exit_code == 0
            assert "Created branch 'test-branch'" in result.output

        # Verify the branch was created with the new commit
        new_branch_path = temp_dir / ".git" / "refs" / "heads" / "test-branch"
        assert new_branch_path.exists()
        with open(new_branch_path, "r") as f:
            assert f.read().strip() == new_commit


# Test for the branch command with errors
@pytest.mark.cli
def test_branch_command_errors(temp_dir: pathlib.Path):
    """
    Test the branch command with various error conditions.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Initialize a repository
        result = runner.invoke(cli, ["init", str(temp_dir)])
        assert result.exit_code == 0

        # Create a commit hash in the main branch
        commit_hash = "1234567890abcdef1234567890abcdef12345678"
        branch_path = temp_dir / ".git" / "refs" / "heads" / "main"
        branch_path.parent.mkdir(parents=True, exist_ok=True)
        with open(branch_path, "w") as f:
            f.write(commit_hash)

        # Create a branch with an invalid name
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(cli, ["branch", "invalid/branch"])
            assert result.exit_code == 0


# Test for the branch command with list option
@pytest.mark.cli
def test_branch_command_list(temp_dir: pathlib.Path):
    """
    Test the branch command with list option.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Initialize a repository
        result = runner.invoke(cli, ["init", str(temp_dir)])
        assert result.exit_code == 0

        # Create a commit hash
        commit_hash = "1234567890abcdef1234567890abcdef12345678"

        # Update the main branch reference
        main_branch_path = temp_dir / ".git" / "refs" / "heads" / "main"
        main_branch_path.parent.mkdir(parents=True, exist_ok=True)
        with open(main_branch_path, "w") as f:
            f.write(commit_hash)

        # Create additional branches
        branch1_path = temp_dir / ".git" / "refs" / "heads" / "branch1"
        with open(branch1_path, "w") as f:
            f.write(commit_hash)

        branch2_path = temp_dir / ".git" / "refs" / "heads" / "branch2"
        with open(branch2_path, "w") as f:
            f.write(commit_hash)

        # List branches
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(cli, ["branch", "--list"])
            assert result.exit_code == 0

            # Check that all branches are listed
            assert "main" in result.output
            assert "branch1" in result.output
            assert "branch2" in result.output


# Test for the branch command with list option and no branches
@pytest.mark.cli
def test_branch_command_list_no_branches(temp_dir: pathlib.Path):
    """
    Test the branch command with list option when no branches exist.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Initialize a repository
        result = runner.invoke(cli, ["init", str(temp_dir)])
        assert result.exit_code == 0

        # Remove the entire refs/heads directory
        heads_dir = temp_dir / ".git" / "refs" / "heads"
        if heads_dir.exists():
            shutil.rmtree(heads_dir)

        # Create an empty heads directory for the test
        heads_dir.mkdir(parents=True, exist_ok=True)

        # List branches
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(cli, ["branch", "--list"])
            assert result.exit_code == 0
            assert "No branches found" in result.output


# Test for the branch command with list option and an exception
@pytest.mark.cli
def test_branch_command_list_exception():
    """
    Test the branch command with list option when an exception occurs.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Mock an exception when listing branches
        with patch(
            "clony.core.refs.list_branches", side_effect=Exception("Test exception")
        ):
            result = runner.invoke(cli, ["branch", "--list"])
            assert result.exit_code == 0
            assert "Error" in result.output


# Test for branch command with no flags or branch name
@pytest.mark.cli
def test_branch_command_no_args():
    """
    Test the branch command when called without any arguments or flags.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["branch"])
        assert result.exit_code == 0
        assert "Branch name is required unless --list is specified" in result.output


# Test for the branch command with delete option
@pytest.mark.cli
def test_branch_command_delete(temp_dir: pathlib.Path):
    """
    Test the branch command with delete option.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Initialize a repository
        result = runner.invoke(cli, ["init", str(temp_dir)])
        assert result.exit_code == 0

        # Create a commit hash
        commit_hash = "1234567890abcdef1234567890abcdef12345678"

        # Update the main branch reference
        main_branch_path = temp_dir / ".git" / "refs" / "heads" / "main"
        main_branch_path.parent.mkdir(parents=True, exist_ok=True)
        with open(main_branch_path, "w") as f:
            f.write(commit_hash)

        # Create a branch to delete
        branch_path = temp_dir / ".git" / "refs" / "heads" / "branch-to-delete"
        with open(branch_path, "w") as f:
            f.write(commit_hash)

        # Delete the branch
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(cli, ["branch", "branch-to-delete", "--delete"])
            assert result.exit_code == 0

        # Verify the branch was deleted
        assert not branch_path.exists()


# Test for the branch command with delete and force options
@pytest.mark.cli
def test_branch_command_delete_force(temp_dir: pathlib.Path):
    """
    Test the branch command with delete and force options.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Initialize a repository
        result = runner.invoke(cli, ["init", str(temp_dir)])
        assert result.exit_code == 0

        # Create a commit hash
        commit_hash = "1234567890abcdef1234567890abcdef12345678"

        # Update the main branch reference
        main_branch_path = temp_dir / ".git" / "refs" / "heads" / "main"
        main_branch_path.parent.mkdir(parents=True, exist_ok=True)
        with open(main_branch_path, "w") as f:
            f.write(commit_hash)

        # Set HEAD to reference main branch
        head_file = temp_dir / ".git" / "HEAD"
        with open(head_file, "w") as f:
            f.write("ref: refs/heads/main\n")

        # Try to delete the current branch without force
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(cli, ["branch", "main", "--delete"])
            assert result.exit_code == 0

        # Verify the branch still exists
        assert main_branch_path.exists()

        # Delete the current branch with force
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(cli, ["branch", "main", "--delete", "--force"])
            assert result.exit_code == 0

        # Verify the branch was deleted
        assert not main_branch_path.exists()


# Test for the branch command with delete option and errors
@pytest.mark.cli
def test_branch_command_delete_errors(temp_dir: pathlib.Path):
    """
    Test the branch command with delete option and various error conditions.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Initialize a repository
        result = runner.invoke(cli, ["init", str(temp_dir)])
        assert result.exit_code == 0

        # Try to delete a non-existent branch
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(cli, ["branch", "non-existent-branch", "--delete"])
            assert result.exit_code == 0


# Test for the branch command with delete option and exception
@pytest.mark.cli
def test_branch_command_delete_exception():
    """
    Test the branch command with delete option when an exception occurs.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Mock an exception when deleting a branch
        with patch(
            "clony.core.refs.delete_branch", side_effect=Exception("Test exception")
        ):
            result = runner.invoke(cli, ["branch", "test-branch", "--delete"])
            assert result.exit_code == 0
            assert "Error" in result.output


# Test for the branch command with an exception
@pytest.mark.cli
def test_branch_command_exception():
    """
    Test the branch command when an exception occurs.
    """

    # Create a repository in the temporary directory
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Mock an exception when creating a branch
        with patch(
            "clony.core.refs.create_branch", side_effect=Exception("Test exception")
        ):
            result = runner.invoke(cli, ["branch", "test-branch"])
            assert result.exit_code == 0
            assert "Error" in result.output
