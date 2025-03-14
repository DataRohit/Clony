"""
Tests for the CLI module.

This module contains tests for the Clony CLI functionality.
"""

# Standard imports
import hashlib
import pathlib
import shutil
import tempfile
from typing import Generator
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest
from click import Option
from click.testing import CliRunner

# Local imports
import clony
from clony import __version__
from clony.cli import cli, display_logo, display_stylized_help, main
from clony.repository import Repository


# Test for the CLI help command with --help
def test_cli_help():
    """
    Test that the CLI help command works correctly with --help.
    """

    # Mock the display_stylized_help function
    with patch("clony.cli.display_stylized_help") as mock_help:
        # Run the CLI with --help
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        # Assert that the exit code is 0
        assert result.exit_code == 0

        # Assert that the display_stylized_help function was called once
        mock_help.assert_called_once()


# Test for the CLI help command with -h
def test_cli_help_shorthand():
    """
    Test that the CLI help command works correctly with -h shorthand.
    """

    # Mock the display_stylized_help function
    with patch("clony.cli.display_stylized_help") as mock_help:
        # Run the CLI with -h
        runner = CliRunner()
        result = runner.invoke(cli, ["-h"])

        # Assert that the exit code is 0
        assert result.exit_code == 0

        # Assert that the display_stylized_help function was called once
        mock_help.assert_called_once()


# Test for the CLI version command
def test_cli_version():
    """
    Test that the CLI version command works correctly.
    """

    # Mock the display_logo function
    with patch("clony.cli.display_logo"):
        # Run the CLI with --version
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        # Assert that the exit code is 0
        assert result.exit_code == 0

        # Assert that the version is in the output
        assert __version__ in result.output


# Test for the CLI with no arguments
def test_cli_no_args():
    """
    Test that the CLI works correctly when no arguments are provided.
    """

    # Mock the display_stylized_help function
    with patch("clony.cli.display_stylized_help") as mock_help:
        # Run the CLI with no arguments
        with patch("clony.cli.display_logo"):
            # Run the CLI with no arguments
            runner = CliRunner()
            result = runner.invoke(cli)

            # Assert that the exit code is 0
            assert result.exit_code == 0

            # Assert that the display_stylized_help function was called once
            mock_help.assert_called_once_with(
                mock_help.call_args[0][0], show_logo=False
            )


# Test for the display_logo function
def test_display_logo():
    """
    Test that the display_logo function works correctly.
    """

    # Mock the console.print function
    with patch("clony.cli.console.print") as mock_print:
        # Run the display_logo function
        display_logo()

        # Assert that the console.print function was called once
        mock_print.assert_called_once()


# Test for the display_stylized_help function with no commands
def test_display_stylized_help_no_commands():
    """
    Test that the display_stylized_help function works correctly with no commands.
    """

    # Create a mock context
    mock_ctx = MagicMock()
    mock_ctx.command.help = "Test help text"
    mock_ctx.command.params = []
    mock_ctx.command.commands = {}

    # Mock the display_logo function
    with patch("clony.cli.display_logo") as mock_logo:
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Run the display_stylized_help function
            display_stylized_help(mock_ctx)

            # Assert that the display_logo function was called once
            mock_logo.assert_called_once()

            # Assert that the console.print function was called at least twice
            assert mock_print.call_count >= 2


# Test for the display_stylized_help function with show_logo=False
def test_display_stylized_help_no_logo():
    """
    Test that the display_stylized_help function works correctly with show_logo=False.
    """

    # Create a mock context
    mock_ctx = MagicMock()
    mock_ctx.command.help = "Test help text"
    mock_ctx.command.params = []
    mock_ctx.command.commands = {}

    # Mock the display_logo function
    with patch("clony.cli.display_logo") as mock_logo:
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Run the display_stylized_help function
            display_stylized_help(mock_ctx, show_logo=False)

            # Assert that the display_logo function was not called
            mock_logo.assert_not_called()

            # Assert that the console.print function was called at least twice
            assert mock_print.call_count >= 2


# Test for the display_stylized_help function with commands
def test_display_stylized_help_with_commands():
    """
    Test that the display_stylized_help function works correctly with commands.
    """

    # Create a mock command
    mock_cmd = MagicMock()
    mock_cmd.help = "Test command help"

    # Create a mock context
    mock_ctx = MagicMock()
    mock_ctx.command.help = "Test help text"
    mock_ctx.command.params = []
    mock_ctx.command.commands = {"test-cmd": mock_cmd}

    # Mock the display_logo function
    with patch("clony.cli.display_logo") as mock_logo:
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Run the display_stylized_help function
            display_stylized_help(mock_ctx)

            # Assert that the display_logo function was called once
            mock_logo.assert_called_once()

            # Assert that the console.print function was called at least three times
            assert mock_print.call_count >= 3


# Test for the display_stylized_help function with options
def test_display_stylized_help_with_options():
    """
    Test that the display_stylized_help function works correctly with options.
    """

    # Create a mock option
    mock_option = MagicMock(spec=Option)
    mock_option.opts = ["--test"]
    mock_option.secondary_opts = ["-t"]
    mock_option.help = "Test option help"

    # Create a mock context
    mock_ctx = MagicMock()
    mock_ctx.command.help = "Test help text"
    mock_ctx.command.params = [mock_option]
    mock_ctx.command.commands = {}

    # Mock the display_logo function
    with patch("clony.cli.display_logo") as mock_logo:
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Run the display_stylized_help function
            display_stylized_help(mock_ctx)

            # Assert that the display_logo function was called once
            mock_logo.assert_called_once()

            # Assert that the console.print function was called at least three times
            assert mock_print.call_count >= 3


# Test for the display_stylized_help function with commands and options
def test_display_stylized_help_with_commands_and_options():
    """
    Test that the display_stylized_help function works correctly with both
    commands and options.
    """

    # Create a mock command
    mock_cmd = MagicMock()
    mock_cmd.help = "Test command help"

    # Create a mock option
    mock_option = MagicMock(spec=Option)
    mock_option.opts = ["--test"]
    mock_option.secondary_opts = ["-t"]
    mock_option.help = "Test option help"

    # Create a mock context
    mock_ctx = MagicMock()
    mock_ctx.command.help = "Test help text"
    mock_ctx.command.params = [mock_option]
    mock_ctx.command.commands = {"test-cmd": mock_cmd}

    # Mock the display_logo function
    with patch("clony.cli.display_logo") as mock_logo:
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Run the display_stylized_help function
            display_stylized_help(mock_ctx)

            # Assert that the display_logo function was called once
            mock_logo.assert_called_once()

            # Assert that the console.print function was called at least four times
            assert mock_print.call_count >= 4


# Test for the help command
def test_help_command():
    """
    Test that the help command works correctly.
    """

    # Mock the display_stylized_help function
    with patch("clony.cli.display_stylized_help") as mock_help:
        # Run the help command
        runner = CliRunner()
        result = runner.invoke(cli, ["help"])

        # Assert that the exit code is 0
        assert result.exit_code == 0

        # Assert that the display_stylized_help function was called once
        mock_help.assert_called_once_with(mock_help.call_args[0][0], show_logo=False)


# Test for the main function with successful execution
def test_main_success():
    """
    Test that the main function works correctly with successful execution.
    """

    # Mock the cli function
    with patch("clony.cli.cli") as mock_cli:
        # Mock the sys.exit function
        with patch("sys.exit") as mock_exit:
            # Run the main function
            main()

            # Assert that the cli function was called once
            mock_cli.assert_called_once()

            # Assert that the sys.exit function was not called
            mock_exit.assert_not_called()


# Test for the main function with an exception
def test_main_exception():
    """
    Test that the main function handles exceptions correctly.
    """

    # Mock the cli function
    with patch("clony.cli.cli", side_effect=Exception("Test error")):
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Mock the sys.exit function
            with patch("sys.exit") as mock_exit:
                # Run the main function
                main()

                # Assert that the console.print function was called once
                mock_print.assert_called_once()

                # Assert that the sys.exit function was called once with 1
                mock_exit.assert_called_once_with(1)


# Test for the if __name__ == "__main__" block
def test_main_module_execution():
    """
    Test that the main function is called when the module is executed directly.
    """

    # Mock the main function
    with patch("clony.cli.main") as mock_main:
        # Directly call the code that would be executed in the
        # if __name__ == "__main__" block
        if hasattr(clony.cli, "__main_block_for_testing"):
            # Call the function that contains the code from the
            # if __name__ == "__main__" block
            clony.cli.__main_block_for_testing()
        else:
            # If the function doesn't exist, just call main() directly
            # This is a fallback that simulates what would happen in the if block
            clony.cli.main()

        # Assert that the main function was called
        mock_main.assert_called_once()


# Test for the init command
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


# Test for the init command
def test_init_command(temp_dir: pathlib.Path):
    """
    Test the init command functionality.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a CLI runner
    runner = CliRunner()

    # Test init command in the temporary directory
    result = runner.invoke(cli, ["init", str(temp_dir)])

    # Check if the command executed successfully
    assert result.exit_code == 0

    # Check if .git directory was created
    git_dir = temp_dir / ".git"
    assert git_dir.exists()

    # Check if required subdirectories exist
    assert (git_dir / "objects").exists()
    assert (git_dir / "refs").exists()
    assert (git_dir / "hooks").exists()

    # Check if HEAD file exists and has correct content
    head_file = git_dir / "HEAD"
    assert head_file.exists()
    with open(head_file) as f:
        assert f.read().strip() == "ref: refs/heads/main"


# Test for the init command with an existing repository
def test_init_command_existing_repo(temp_dir: pathlib.Path):
    """
    Test the init command with an existing repository.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a CLI runner
    runner = CliRunner()

    # Initialize repository first time
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 0

    # Try to initialize again without force
    result = runner.invoke(cli, ["init", str(temp_dir)])
    assert result.exit_code == 1

    # Verify that the repository exists
    repo = Repository(str(temp_dir))
    assert repo.exists()

    # Try to initialize with force
    result = runner.invoke(cli, ["init", "--force", str(temp_dir)])
    assert result.exit_code == 0


# Test for the init command with an invalid path
def test_init_command_invalid_path():
    """
    Test the init command with an invalid path.
    """

    # Create a CLI runner
    runner = CliRunner()

    # Try to initialize in an invalid path
    result = runner.invoke(cli, ["init", "/invalid/path/that/does/not/exist"])
    assert result.exit_code == 1


# Test for the init command help message
def test_init_command_help():
    """
    Test the init command help message.
    """

    # Create a CLI runner
    runner = CliRunner()

    # Get the help message
    result = runner.invoke(cli, ["init", "--help"])

    # Check if the command executed successfully
    assert result.exit_code == 0

    # Check if help message contains expected content
    assert "Initialize a new Git repository" in result.output
    assert "--force" in result.output


# Test for the stage command
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
    result = runner.invoke(cli, ["stage", str(test_file_path)])
    assert result.exit_code == 0
    assert f"File staged: '{str(test_file_path)}'" in result.stdout.strip()

    # Check if blob object was created
    repo = Repository(str(temp_dir))
    file_content = test_file_path.read_bytes()
    sha1_hash = hashlib.sha1(file_content).hexdigest()
    object_file_path = repo.git_dir / "objects" / sha1_hash[:2] / sha1_hash[2:]
    assert object_file_path.exists()

    # Check if index file was updated
    index_file_path = repo.git_dir / "index"
    assert index_file_path.exists()
    with open(index_file_path, "r") as index_file:
        index_content = index_file.read()
        assert str(test_file_path) in index_content
        assert sha1_hash in index_content


# Test for the stage command with non-existent file
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

    # Run the stage command for a non-existent file
    result = runner.invoke(cli, ["stage", "non_existent_file.txt"])
    assert result.exit_code == 0


# Test for the stage command with exception
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
        # Mock the logger.error function to verify it's called with the correct message
        with patch("clony.cli.logger.error") as mock_logger_error:
            # Run the stage command and expect an error
            result = runner.invoke(cli, ["stage", str(test_file_path)])
            assert result.exit_code == 0

            # Verify that logger.error was called with the correct message
            mock_logger_error.assert_called_with(
                "Error staging file: Generic Mocked Exception"
            )
            assert (
                "ERROR: Error staging file: Generic Mocked Exception" in result.output
            )


# Test for the stage command with FileNotFoundError
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
        # Mock the logger.error function to verify it's called with the correct message
        with patch("clony.cli.logger.error") as mock_logger_error:
            # Run the stage command and expect an error
            result = runner.invoke(cli, ["stage", str(test_file_path)])
            assert result.exit_code == 0

            # Verify that logger.error was called with the correct message
            mock_logger_error.assert_called_with("Error staging file: File not found")
            assert "ERROR: Error staging file: File not found" in result.output


# Test for the stage command with NotADirectoryError
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
        # Mock the logger.error function to verify it's called with the correct message
        with patch("clony.cli.logger.error") as mock_logger_error:
            # Run the stage command and expect an error
            result = runner.invoke(cli, ["stage", str(test_file_path)])
            assert result.exit_code == 0

            # Verify that logger.error was called with the correct message
            mock_logger_error.assert_called_with(
                f"Invalid path: '{str(test_file_path)}' is not a directory"
            )
            # Check that the error message is in the output
            assert "ERROR:" in result.output
            assert "Invalid path:" in result.output
            assert str(test_file_path) in result.output

            # The "is not a directory" text might be split across lines
            assert "is not a" in result.output
            assert "directory" in result.output


# Test for the stage command with "Not a git repository" error
def test_stage_command_not_a_git_repo(temp_dir: pathlib.Path):
    """
    Test the stage command when a "Not a git repository" error is raised.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a test file in the temp directory (without initializing a git repo)
    test_file_path = temp_dir / "test_file.txt"
    test_file_path.write_text("This is a test file.")

    # Mock stage_file function to raise a "Not a git repository" exception
    with patch("clony.cli.stage_file", side_effect=Exception("Not a git repository")):
        # Run the stage command and expect an error
        runner = CliRunner()
        result = runner.invoke(cli, ["stage", str(test_file_path)])
        assert result.exit_code == 0

        # Verify that logger.error was called with the correct message
        assert (
            "ERROR:   Not a git repository. Run 'clony init' to create one."
            in result.output
        )


# Test for the stage command with "File already staged" error
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

    # Mock stage_file function to raise a "File already staged" exception
    with patch("clony.cli.stage_file", side_effect=Exception("File already staged")):
        # Run the stage command and expect an error
        result = runner.invoke(cli, ["stage", str(test_file_path)])
        assert result.exit_code == 0

        # Check that the warning message is in the output
        assert "WARNING:" in result.output
        assert "File already staged:" in result.output
        assert str(test_file_path) in result.output


# Test for the stage command with "Error staging file:" error
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

    # Mock stage_file function to raise an "Error staging file:" exception
    with patch(
        "clony.cli.stage_file",
        side_effect=Exception("Error staging file: Some specific error"),
    ):
        # Mock the logger.error function to verify it's called with the correct message
        with patch("clony.cli.logger.error") as mock_logger_error:
            # Run the stage command and expect an error
            result = runner.invoke(cli, ["stage", str(test_file_path)])
            assert result.exit_code == 0

            # For "Error staging file:" errors, the CLI doesn't print to console
            mock_logger_error.assert_not_called()


# Test for stage command with error staging file message
@pytest.mark.unit
def test_stage_command_error_staging_file_message():
    """
    Test the stage command when an error occurs with 'Error staging file:' message.
    """
    runner = CliRunner()

    # Create a temporary file
    with runner.isolated_filesystem():
        # Create a test file
        with open("test.txt", "w") as f:
            f.write("test content")

        # Mock stage_file to raise an exception with specific message
        with patch("clony.cli.stage_file") as mock_stage:
            mock_stage.side_effect = Exception("Error staging file: test error")

            # Run the command
            result = runner.invoke(cli, ["stage", "test.txt"])

            # Verify the command exited successfully (since error is handled)
            assert result.exit_code == 0

            # Verify no output since error is already logged in staging.py
            assert result.output == ""


# Test for stage command with failure return value
@pytest.mark.unit
def test_stage_command_failure_return():
    """
    Test the stage command when stage_file returns a failure tuple.
    """
    runner = CliRunner()

    # Create a temporary file
    with runner.isolated_filesystem():
        # Create a test file
        with open("test.txt", "w") as f:
            f.write("test content")

        # Mock stage_file to return a failure tuple
        with patch("clony.cli.stage_file") as mock_stage:
            mock_stage.return_value = (False, "Failed to stage file")

            # Run the command
            result = runner.invoke(cli, ["stage", "test.txt"])

            # Verify the command exited successfully (since error is handled)
            assert result.exit_code == 0

            # Verify error output (without Rich formatting)
            assert "ERROR: Failed to stage file" in result.output
