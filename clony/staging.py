"""
Staging module for Clony.

This module handles the staging of files for the Clony Git clone tool.
"""

# Standard library imports
import hashlib
import zlib
from pathlib import Path

# Local imports
from clony.logger import logger


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

    for line in lines:
        parts = line.strip().split()
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
        parts = line.strip().split()
        if len(parts) == 2 and parts[0] == file_path:
            # If the file is in the index, check if the hash matches
            return parts[1] == current_hash

    # If the file is not in the index, it's not staged
    return False


# Function to stage a file
def stage_file(file_path: str) -> None:
    """Stage a file by creating a blob object and updating the index."""

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
            # If no git repo found, log error and raise exception
            logger.error("Not a git repository")
            raise Exception("Not a git repository")

        object_dir = repo_path / ".git" / "objects"
        index_file = repo_path / ".git" / "index"

        # Check if the file is already staged
        if is_file_already_staged(index_file, str(file_path_obj), sha1_hash):
            # If the file is already staged, log warning and raise exception
            logger.warning(f"File already staged: '{file_path}'")
            raise Exception("File already staged")

        # Ensure objects directory exists
        object_dir.mkdir(parents=True, exist_ok=True)

        # Ensure index file exists
        index_file.touch(exist_ok=True)

        # Write blob object
        write_object_file(object_dir, sha1_hash, compressed_content)

        # Update index file
        update_index_file(index_file, file_path, sha1_hash)

    except Exception as e:
        # Log the error if it's not already logged
        if str(e) != "Not a git repository" and str(e) != "File already staged":
            logger.error(f"Error staging file: {e}")

        # Raise the error with the expected format for tests
        if str(e) == "Not a git repository" or str(e) == "File already staged":
            # Re-raise the original exception for known cases
            raise
        else:
            # For other errors, wrap them in the expected format
            raise Exception(f"Error staging file: {e}")
