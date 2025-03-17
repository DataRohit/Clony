"""
Tests for the Git repository functionality.

This module contains tests for the Repository class and its methods.
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
from clony.core.repository import Repository


# Test for the Repository class
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


# Test for the initialization of a new repository
def test_repository_initialization(temp_dir: pathlib.Path):
    """
    Test the initialization of a new repository.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a new repository instance
    repo = Repository(str(temp_dir))

    # Initialize the repository
    assert repo.init() is True

    # Check if .git directory exists
    assert repo.git_dir.exists()

    # Check if required subdirectories exist
    assert repo.objects_dir.exists()
    assert repo.refs_dir.exists()
    assert repo.hooks_dir.exists()

    # Check if HEAD file exists and has correct content
    assert repo.head_file.exists()
    with open(repo.head_file) as f:
        assert f.read().strip() == "ref: refs/heads/main"

    # Check if refs/heads and refs/tags directories exist
    assert (repo.refs_dir / "heads").exists()
    assert (repo.refs_dir / "tags").exists()

    # Check if config file exists and has correct content
    config_file = repo.git_dir / "config"
    assert config_file.exists()
    with open(config_file) as f:
        config_content = f.read()
        assert "[core]" in config_content
        assert "repositoryformatversion = 0" in config_content
        assert "filemode = true" in config_content
        assert "bare = false" in config_content
        assert "logallrefupdates = true" in config_content


# Test for the repository existence check
def test_repository_exists(temp_dir: pathlib.Path):
    """
    Test the repository existence check.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a new repository instance
    repo = Repository(str(temp_dir))

    # Check that repository doesn't exist initially
    assert repo.exists() is False

    # Initialize the repository
    repo.init()

    # Check that repository exists after initialization
    assert repo.exists() is True


# Test for the force reinitialization of an existing repository
def test_repository_force_reinitialization(temp_dir: pathlib.Path):
    """
    Test force reinitialization of an existing repository.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a new repository instance
    repo = Repository(str(temp_dir))

    # Initialize the repository
    assert repo.init() is True

    # Try to initialize again without force
    assert repo.init() is False

    # Try to initialize with force
    assert repo.init(force=True) is True


# Test for the repository initialization with an invalid path
def test_repository_invalid_path():
    """
    Test repository initialization with an invalid path.
    """

    # Create a repository instance with an invalid path
    repo = Repository("/invalid/path/that/does/not/exist")

    # Try to initialize the repository
    assert repo.init() is False


# Test for repository initialization exception
def test_repository_initialization_exception(temp_dir: pathlib.Path):
    """
    Test repository initialization exception handling.

    Args:
        temp_dir: Path to the temporary directory.
    """

    # Create a new repository instance
    repo = Repository(str(temp_dir))

    # Mock mkdir to raise an exception
    with patch("pathlib.Path.mkdir", side_effect=OSError("Mocked OSError")):
        # Try to initialize the repository and expect failure
        assert repo.init() is False

    # Assert that repository does not exist
    assert not repo.exists()

    # Assert that .git directory does not exist
    assert not repo.git_dir.exists()
