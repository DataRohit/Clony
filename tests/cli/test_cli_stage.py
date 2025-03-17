"""
Tests for the CLI stage command.

This module contains tests for the Clony CLI stage command.
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


# Test for the stage command
@pytest.mark.cli
def test_stage_command(temp_dir: pathlib.Path):
    """
    Test the stage command functionality.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Create a test file in the temp directory
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file.")

    # Run the stage command for the test file
    with patch("clony.cli.stage_file") as mock_stage_file:
        # Run the stage command
        result = runner.invoke(cli, ["stage", str(test_file_path)])

        # Assert that the command exited with a success code
        assert result.exit_code == 0

        # Assert that the stage_file function was called once with the correct path
        mock_stage_file.assert_called_once_with(str(test_file_path))


# Test for the stage command with non-existent file
@pytest.mark.cli
def test_stage_command_non_existent_file(temp_dir: pathlib.Path):
    """
    Test the stage command with a non-existent file.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Define a non-existent file path
    non_existent_file = temp_dir / "non_existent_file.txt"

    # Run the stage command with a non-existent file
    with patch("clony.cli.logger.error") as mock_logger_error:
        # Run the stage command
        result = runner.invoke(cli, ["stage", str(non_existent_file)])

        # Assert that the logger.error function was called with the correct path
        mock_logger_error.assert_called_with(f"File not found: '{non_existent_file}'")


# Test for the stage command with a generic exception
@pytest.mark.cli
def test_stage_command_exception(temp_dir: pathlib.Path):
    """
    Test the stage command with a generic exception.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Create a test file in the temp directory
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file.")

    # Mock stage_file function to raise a generic exception
    with patch(
        "clony.cli.stage_file", side_effect=Exception("Generic Mocked Exception")
    ):
        # Run the stage command and expect an error
        result = runner.invoke(cli, ["stage", str(test_file_path)])

        # Verify that the command exited with an error
        assert result.exit_code != 0


# Test for the stage command when a FileNotFoundError is raised
@pytest.mark.cli
def test_stage_command_file_not_found_error(temp_dir: pathlib.Path):
    """
    Test the stage command when a FileNotFoundError is raised.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Create a test file that actually exists (to pass Click's validation)
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file.")

    # Mock stage_file function to raise a FileNotFoundError
    with patch("clony.cli.stage_file", side_effect=FileNotFoundError("File not found")):
        # Run the stage command and expect an error
        result = runner.invoke(cli, ["stage", str(test_file_path)])

        # Verify that the command exited with an error
        assert result.exit_code != 0


# Test for the stage command when a NotADirectoryError is raised
@pytest.mark.cli
def test_stage_command_not_a_directory_error(temp_dir: pathlib.Path):
    """
    Test the stage command when a NotADirectoryError is raised.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Create a test file in the temp directory
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file.")

    # Mock stage_file function to raise a NotADirectoryError
    with patch(
        "clony.cli.stage_file", side_effect=NotADirectoryError("Not a directory")
    ):
        # Run the stage command and expect an error
        result = runner.invoke(cli, ["stage", str(test_file_path)])

        # Verify that the command exited with an error
        assert result.exit_code != 0


# Test for the stage command when a "Not a git repository" error is raised
@pytest.mark.cli
def test_stage_command_not_a_git_repo(temp_dir: pathlib.Path):
    """
    Test the stage command when a "Not a git repository" error is raised.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a test file in the temp directory (without initializing a git repo)
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file.")

    # Mock stage_file function to exit with a SystemExit
    with patch("clony.cli.stage_file", side_effect=SystemExit(1)):
        # Run the stage command and expect an error
        runner = CliRunner()

        # Run the stage command
        result = runner.invoke(cli, ["stage", str(test_file_path)])

        # Verify that the command exited with an error
        assert result.exit_code != 0


# Test for the stage command when a "File already staged" warning is logged
@pytest.mark.cli
def test_stage_command_file_already_staged(temp_dir: pathlib.Path):
    """
    Test the stage command when a "File already staged" error is raised.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Create a test file in the temp directory
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file.")

    # Mock stage_file function to call logger.warning with "File already staged"
    with patch("clony.cli.stage_file") as mock_stage_file:
        # Set up the side effect to call a function that logs a warning
        def side_effect(path):
            from clony.utils.logger import logger

            # Log the warning
            logger.warning(f"File already staged: '{path}'")

        # Set the side effect to call the function that logs a warning
        mock_stage_file.side_effect = side_effect

        # Run the stage command
        result = runner.invoke(cli, ["stage", str(test_file_path)])

        # Verify that the command executed successfully
        assert result.exit_code == 0

        # Verify that the mock was called with the correct path
        mock_stage_file.assert_called_with(str(test_file_path))


# Test for the stage command when an "Error staging file:" error is raised
@pytest.mark.cli
def test_stage_command_error_staging_file(temp_dir: pathlib.Path):
    """
    Test the stage command when an "Error staging file:" error is raised.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Create a test file in the temp directory
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file.")

    # Mock stage_file function to call logger.error with "Error staging file"
    with patch("clony.cli.stage_file") as mock_stage_file:
        # Set up the side effect to call a function that logs an error
        def side_effect(path):
            from clony.utils.logger import logger

            # Log the error
            logger.error(f"Error staging file: '{path}'")

            # Raise a SystemExit
            raise SystemExit(1)

        # Set the side effect to call the function that logs an error
        mock_stage_file.side_effect = side_effect

        # Run the stage command and expect an error
        result = runner.invoke(cli, ["stage", str(test_file_path)])

        # Verify that the command exited with an error
        assert result.exit_code != 0

        # Verify that the mock was called with the correct path
        mock_stage_file.assert_called_with(str(test_file_path))


# Test for the stage command when an error occurs with 'Error staging file:' message
@pytest.mark.cli
def test_stage_command_error_staging_file_message():
    """
    Test the stage command when an error occurs with 'Error staging file:' message.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()

    # Create a temporary file
    with runner.isolated_filesystem():
        # Create a test file
        with open("test.txt", "w") as f:
            f.write("test content")

        # Mock stage_file to log an error and exit
        with patch("clony.cli.stage_file") as mock_stage:
            # Set up the side effect to call a function that logs an error
            def side_effect(path):
                # Log the error
                from clony.utils.logger import logger

                # Log the error
                logger.error(f"Error staging file: '{path}'")

                # Raise a SystemExit
                raise SystemExit(1)

            # Set the side effect to call the function that logs an error
            mock_stage.side_effect = side_effect

            # Run the command
            result = runner.invoke(cli, ["stage", "test.txt"])

            # Verify that the command exited with an error
            assert result.exit_code != 0

            # Verify that the mock was called with the correct path
            mock_stage.assert_called_with("test.txt")


# Test for the stage command when stage_file raises a SystemExit
@pytest.mark.cli
def test_stage_command_failure_return():
    """
    Test the stage command when stage_file raises a SystemExit.
    """

    # Initialize a git repository in the temp directory
    runner = CliRunner()

    # Create a temporary file
    with runner.isolated_filesystem():
        # Create a test file
        with open("test.txt", "w") as f:
            f.write("test content")

        # Mock stage_file to raise SystemExit
        with patch("clony.cli.stage_file", side_effect=SystemExit(1)):
            # Run the command
            result = runner.invoke(cli, ["stage", "test.txt"])

            # Verify that the command exited with an error
            assert result.exit_code != 0
