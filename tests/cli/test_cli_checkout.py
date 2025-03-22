"""
Tests for the checkout CLI command.
"""

# Standard library imports
from unittest.mock import patch

# Third-party imports
from click.testing import CliRunner

# Local imports
from clony.cli import checkout


# Test checkout command with branch
@patch("clony.cli.switch_branch_or_commit")
def test_checkout_branch(mock_switch_branch_or_commit):
    """
    Test that checkout command correctly switches to a branch.
    """

    # Setup mocks
    mock_switch_branch_or_commit.return_value = True

    # Setup CLI runner
    runner = CliRunner()

    # Run the command
    result = runner.invoke(checkout, ["main"])

    # Assert the command ran successfully
    assert result.exit_code == 0

    # Verify mock calls
    mock_switch_branch_or_commit.assert_called_once_with("main", False)


# Test checkout command with files
@patch("clony.cli.restore_files")
def test_checkout_files(mock_restore_files):
    """
    Test that checkout command correctly restores files.
    """

    # Setup mocks
    mock_restore_files.return_value = True

    # Setup CLI runner
    runner = CliRunner()

    # Run the command
    result = runner.invoke(checkout, ["main", "file1.txt", "file2.txt"])

    # Assert the command ran successfully
    assert result.exit_code == 0

    # Verify mock calls
    mock_restore_files.assert_called_once_with(
        ["file1.txt", "file2.txt"], "main", force=False
    )


# Test checkout command with force option
@patch("clony.cli.switch_branch_or_commit")
def test_checkout_force(mock_switch_branch_or_commit):
    """
    Test that checkout command correctly passes the force option.
    """

    # Setup mocks
    mock_switch_branch_or_commit.return_value = True

    # Setup CLI runner
    runner = CliRunner()

    # Run the command
    result = runner.invoke(checkout, ["main", "--force"])

    # Assert the command ran successfully
    assert result.exit_code == 0

    # Verify mock calls
    mock_switch_branch_or_commit.assert_called_once_with("main", True)


# Test checkout command failure
@patch("clony.cli.switch_branch_or_commit")
def test_checkout_failure(mock_switch_branch_or_commit):
    """
    Test that checkout command handles failure correctly.
    """

    # Setup mocks
    mock_switch_branch_or_commit.return_value = False

    # Setup CLI runner
    runner = CliRunner()

    # Run the command
    result = runner.invoke(checkout, ["main"])

    # Assert the command failed with exit code 1
    assert result.exit_code == 1

    # Verify mock calls
    mock_switch_branch_or_commit.assert_called_once_with("main", False)


# Test checkout command with files failure
@patch("clony.cli.restore_files")
def test_checkout_files_failure(mock_restore_files):
    """
    Test that checkout command handles file restoration failure correctly.
    """

    # Setup mocks
    mock_restore_files.return_value = False

    # Setup CLI runner
    runner = CliRunner()

    # Run the command
    result = runner.invoke(checkout, ["main", "file1.txt"])

    # Assert the command failed with exit code 1
    assert result.exit_code == 1

    # Verify mock calls
    mock_restore_files.assert_called_once_with(["file1.txt"], "main", force=False)


# Test checkout command with force option for files
@patch("clony.cli.restore_files")
def test_checkout_files_force(mock_restore_files):
    """
    Test that checkout command correctly passes the force option when restoring files.
    """

    # Setup mocks
    mock_restore_files.return_value = True

    # Setup CLI runner
    runner = CliRunner()

    # Run the command
    result = runner.invoke(checkout, ["main", "file1.txt", "--force"])

    # Assert the command ran successfully
    assert result.exit_code == 0

    # Verify mock calls
    mock_restore_files.assert_called_once_with(["file1.txt"], "main", force=True)
