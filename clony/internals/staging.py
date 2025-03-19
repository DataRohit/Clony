"""
Staging module for Clony.

This module handles the staging of files for the Clony Git clone tool.
"""

# Standard library imports
import hashlib
import sys
import zlib
from pathlib import Path

from rich.console import Console
from rich.table import Table

# Local imports
from clony.utils.logger import logger

# Initialize console for Rich
console = Console()


# Function to find the .git repository path
def find_git_repo_path(path: Path) -> Path | None:
    """
    Find the .git repository path by traversing up the directory tree.
    """

    # Resolve the path to an absolute path
    current_path = path.resolve()

    # Traverse up the directory tree until the .git directory is found
    while current_path != current_path.parent:
        # Check if the .git directory exists
        if (current_path / ".git").is_dir():
            return current_path

        # Traverse to the parent directory
        current_path = current_path.parent

    # Log the failure to find the .git directory
    logger.debug(f"Failed to find .git directory for path: {path}")

    # Return None if the .git directory is not found
    return None


# Function to calculate the SHA-1 hash of the content
def calculate_sha1_hash(content: bytes) -> str:
    """
    Calculate the SHA-1 hash of the given content.
    Args:
        content (bytes): The content to hash.

    Returns:
        str: The SHA-1 hash of the content.
    """

    # Calculate the SHA-1 hash of the content
    sha1_hash = hashlib.sha1(content).hexdigest()

    # Return the SHA-1 hash
    return sha1_hash


# Function to compress content using zlib
def compress_content(content: bytes) -> bytes:
    """Compress content using zlib."""

    # Compress the content using zlib
    return zlib.compress(content)


# Function to write the object file
def write_object_file(
    object_dir: Path, sha1_hash: str, compressed_content: bytes
) -> None:
    """
    Write the compressed content to an object file in the .git/objects directory.
    Args:
        object_dir (Path): Path to the .git/objects directory.
        sha1_hash (str): SHA-1 hash of the content, used for naming the file.
        compressed_content (bytes): The compressed content to write.
    """

    # Create the object directory if it doesn't exist
    object_subdir = object_dir / sha1_hash[:2]
    object_subdir.mkdir(parents=True, exist_ok=True)
    object_file_path = object_subdir / sha1_hash[2:]

    # Write the compressed content to the object file
    with open(object_file_path, "wb") as f:
        # Write the compressed content to the object file
        f.write(compressed_content)

    # Log the successful write to the object file
    logger.debug(f"Wrote object file: {object_file_path}")


# Function to update the index file
def update_index_file(index_file: Path, file_path: str, sha1_hash: str) -> None:
    """
    Update the index file with the file path and its SHA-1 hash.
    Args:
        index_file (Path): Path to the .git/index file.
        file_path (str): Path to the file being staged.
        sha1_hash (str): SHA-1 hash of the file content.
    """

    # Read existing index content if the file exists
    if index_file.exists():
        with open(index_file, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    # Check if the file is already in the index
    file_found = False
    new_lines = []

    # Iterate over the lines in the index file
    for line in lines:
        # Split the line into parts
        parts = line.strip().split()

        # If the line has two parts and the first part is the file path,
        # update the entry with the new hash
        if len(parts) == 2 and parts[0] == file_path:
            # Update the existing entry with the new hash
            new_lines.append(f"{file_path} {sha1_hash}\n")
            file_found = True
        else:
            # Keep other entries unchanged
            new_lines.append(line)

    # If the file wasn't found, add it
    if not file_found:
        new_lines.append(f"{file_path} {sha1_hash}\n")

    # Write the updated content back to the index file
    with open(index_file, "w") as f:
        f.writelines(new_lines)

    # Log the successful update to the index file
    logger.debug(f"Updated index file: {index_file}")


# Function to check if a file is already staged
def is_file_already_staged(index_file: Path, file_path: str, current_hash: str) -> bool:
    """
    Check if a file is already staged in the index with the same content.

    Args:
        index_file (Path): Path to the .git/index file.
        file_path (str): Path to the file to check.
        current_hash (str): SHA-1 hash of the current file content.

    Returns:
        bool: True if the file is already staged with the same content, False otherwise.
    """
    # If the index file doesn't exist, the file is not staged
    if not index_file.exists():
        return False

    # Read the index file
    with open(index_file, "r") as f:
        index_content = f.readlines()

    # Check if the file path is in the index with the same hash
    for line in index_content:
        # Split the line into parts
        parts = line.strip().split()

        # If the line has two parts and the first part is the file path,
        # check if the hash matches
        if len(parts) == 2 and parts[0] == file_path:
            # If the file is in the index, check if the hash matches
            return parts[1] == current_hash

    # If the file is not in the index, it's not staged
    return False


# Function to stage a file
def stage_file(file_path: str) -> None:
    """
    Stage a file by creating a blob object and updating the index.

    This function creates a blob object from the file content, adds it to the
    Git objects directory, and updates the index to track the staging. It also
    displays the staging information in a tabular format.

    Args:
        file_path (str): Path to the file to stage.
    """
    try:
        # Convert file path to Path object
        file_path_obj = Path(file_path)

        # Read the content of the file
        with open(file_path_obj, "rb") as f:
            # Read file content as bytes
            content = f.read()

        # Calculate SHA-1 hash of the content
        sha1_hash = calculate_sha1_hash(content)

        # Compress the content
        compressed_content = compress_content(content)

        # Define repository paths
        repo_path = find_git_repo_path(file_path_obj)
        if not repo_path:
            # If no git repo found, return error
            logger.error("Not a git repository. Run 'clony init' to create one.")
            return

        # Define repository paths
        object_dir = repo_path / ".git" / "objects"
        index_file = repo_path / ".git" / "index"

        # Check if the file is already staged
        if is_file_already_staged(index_file, str(file_path_obj), sha1_hash):
            # If the file is already staged, show staging info with UNCHANGED status
            logger.warning(f"File already staged: '{file_path}'")
            display_staging_info(file_path, sha1_hash, "UNCHANGED")
            return

        # Check if the object file exists in the objects directory
        # with the same hash as the current content
        object_subdir = object_dir / sha1_hash[:2]
        object_file = object_subdir / sha1_hash[2:]

        # If the object file exists, the file hasn't changed since the last commit
        if object_file.exists():
            logger.warning(f"File unchanged since last commit: '{file_path}'")
            display_staging_info(file_path, sha1_hash, "UNCHANGED")
            return

        # Ensure objects directory exists
        object_dir.mkdir(parents=True, exist_ok=True)

        # Ensure index file exists
        index_file.touch(exist_ok=True)

        # Write blob object
        write_object_file(object_dir, sha1_hash, compressed_content)

        # Update index file
        update_index_file(index_file, file_path, sha1_hash)

        # Log the successful staging of the file
        logger.info(f"File staged: '{file_path}'")

        # Display staging info with STAGED status
        display_staging_info(file_path, sha1_hash, "STAGED")

    except Exception as e:
        # Log the error and exit
        logger.error(f"Error staging file: {e}")
        sys.exit(1)


# Function to clear the staging area
def clear_staging_area(repo_path: Path) -> None:
    """
    Clear the staging area by removing all entries from the index file.

    Args:
        repo_path (Path): Path to the repository.
    """
    # Define the index file path
    index_file = repo_path / ".git" / "index"

    # If the index file exists, clear it
    if index_file.exists():
        # Write an empty file
        with open(index_file, "w") as f:
            f.write("")

        # Log the successful clearing of the staging area
        logger.debug(f"Cleared staging area: {index_file}")


# Function to check if a file has changed since the last commit
def has_file_changed_since_commit(
    repo_path: Path, file_path: str, current_hash: str
) -> bool:
    """
    Check if a file has changed since the last commit.

    Args:
        repo_path (Path): Path to the repository.
        file_path (str): Path to the file.
        current_hash (str): Current SHA-1 hash of the file content.

    Returns:
        bool: True if the file has changed, False otherwise.
    """
    try:
        # Convert paths to Path objects
        repo_path = Path(repo_path)
        file_path_obj = Path(file_path)

        logger.debug(
            f"has_file_changed_since_commit: repo_path={repo_path}, "
            f"file_path={file_path}, current_hash={current_hash}"
        )

        try:
            # Check if the file is within the repository
            _ = file_path_obj.relative_to(repo_path)
        except ValueError:
            # If the file is not in the repository, consider it changed
            logger.debug(
                "has_file_changed_since_commit: file is not in repository, "
                "returning True"
            )
            return True

        # Define the object file path
        objects_dir = repo_path / ".git" / "objects"
        object_subdir = objects_dir / current_hash[:2]
        object_file = object_subdir / current_hash[2:]

        # Log the object file path
        logger.debug(
            f"has_file_changed_since_commit: checking if object file exists: "
            f"{object_file}"
        )

        # Log if the object file exists
        logger.debug(
            f"has_file_changed_since_commit: object file exists: {object_file.exists()}"
        )

        # If the object file doesn't exist, the file has changed
        if not object_file.exists():
            logger.debug(
                "has_file_changed_since_commit: object file does not exist, "
                "returning True"
            )
            return True

        # Log the file has not changed
        logger.debug(
            "has_file_changed_since_commit: object file exists, returning False"
        )
        return False
    except Exception as e:
        # If there's an error, assume the file has changed
        logger.debug(f"Error checking if file has changed: {e}")
        return True


# Function to display staging information in a tabular format
def display_staging_info(file_path: str, file_hash: str, status: str) -> None:
    """
    Display staging information in a formatted table.

    This function creates and displays a formatted table showing details of
    the staging operation, including file path, hash, and status.

    Args:
        file_path (str): The path of the staged file.
        file_hash (str): The hash of the staged file content.
        status (str): The status of the staging operation (e.g., "STAGED", "UNCHANGED").
    """
    # Create a table for displaying staging information
    table = Table(title="Staging Results")

    # Add columns to the table
    table.add_column("File Path", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Content Hash", style="green")

    # Add the staging information to the table
    table.add_row(
        file_path, status, file_hash[:8]  # Use only the first 8 characters of the hash
    )

    # Display the staging information table
    console.print(table)
