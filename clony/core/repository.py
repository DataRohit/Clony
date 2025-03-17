"""
Git repository functionality for Clony.

This module provides the core functionality for Git repository operations,
including initialization and management of Git repositories.
"""

# Standard library imports
import pathlib

# Third party imports
from rich.console import Console

# Local imports
from clony.utils.logger import logger

# Initialize rich console for pretty output
console = Console()


# Repository class
class Repository:
    """
    A class representing a Git repository.

    This class handles the initialization and management of Git repositories,
    including the creation of necessary directories and files.
    """

    # Initialize a new Repository instance
    def __init__(self, path: str):
        """
        Initialize a new Repository instance.

        Args:
            path: The path where the repository should be created.
        """

        # Convert the path to a Path object for easier manipulation
        self.path = pathlib.Path(path)

        # Define the .git directory path
        self.git_dir = self.path / ".git"

        # Define required subdirectories
        self.objects_dir = self.git_dir / "objects"
        self.refs_dir = self.git_dir / "refs"
        self.hooks_dir = self.git_dir / "hooks"

        # Define the HEAD file path
        self.head_file = self.git_dir / "HEAD"

    # Initialize a new Git repository
    def init(self, force: bool = False) -> bool:
        """
        Initialize a new Git repository.

        This method creates the necessary directory structure and files
        for a new Git repository.

        Args:
            force: Whether to force reinitialization if repository exists.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """

        try:
            # Check if repository exists and force is not set
            if self.exists() and not force:
                return False

            # Check if parent directory exists and is writable
            if not self.path.parent.exists():
                logger.error(f"Parent directory does not exist: {self.path.parent}")
                return False

            # Create the .git directory
            self.git_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Created .git directory")

            # Create required subdirectories
            self.objects_dir.mkdir(exist_ok=True)
            self.refs_dir.mkdir(exist_ok=True)
            self.hooks_dir.mkdir(exist_ok=True)
            logger.debug("Created required subdirectories")

            # Create the HEAD file with default branch reference
            with open(self.head_file, "w") as f:
                f.write("ref: refs/heads/main\n")
            logger.debug("Created HEAD file")

            # Create the refs/heads directory
            (self.refs_dir / "heads").mkdir(exist_ok=True)

            # Create the refs/tags directory
            (self.refs_dir / "tags").mkdir(exist_ok=True)
            logger.debug("Created refs directories")

            # Create a basic config file
            config_file = self.git_dir / "config"
            with open(config_file, "w") as f:
                f.write("[core]\n")
                f.write("    repositoryformatversion = 0\n")
                f.write("    filemode = true\n")
                f.write("    bare = false\n")
                f.write("    logallrefupdates = true\n")
            logger.debug("Created config file")

            # Log successful initialization
            logger.info("Git repository initialized successfully")
            return True

        except Exception as e:
            # Log error and return False
            logger.error(f"Error initializing repository: {str(e)}")
            return False

    # Check if a Git repository already exists at the specified path
    def exists(self) -> bool:
        """
        Check if a Git repository already exists at the specified path.

        Returns:
            bool: True if a repository exists, False otherwise.
        """

        # Return True if the repository exists
        return self.git_dir.exists() and (self.git_dir / "HEAD").exists()
