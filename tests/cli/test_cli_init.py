"""
Tests for the CLI init command.

This module contains tests for the Clony CLI init command.
"""

# Standard imports
import pathlib
import shutil
import tempfile
from typing import Generator

# Third-party imports
import pytest
from click.testing import CliRunner

# Local imports
from clony.cli import cli
from clony.core.repository import Repository


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
@pytest.mark.cli
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
@pytest.mark.cli
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
@pytest.mark.cli
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
@pytest.mark.cli
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
