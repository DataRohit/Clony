"""
Git objects functionality for Clony.

This module provides the core functionality for Git objects, including blob, tree,
and commit objects.
"""

# Standard library imports
import hashlib
import os
import stat
import time
import zlib
from pathlib import Path
from typing import List, Optional, Tuple

# Local imports
from clony.utils.logger import logger


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
    """
    Compress content using zlib.

    Args:
        content (bytes): The content to compress.

    Returns:
        bytes: The compressed content.
    """

    # Compress the content using zlib
    return zlib.compress(content)


# Function to write the object file
def write_object_file(repo_path: Path, content: bytes, object_type: str) -> str:
    """
    Write a Git object to the .git/objects directory.

    Args:
        repo_path (Path): Path to the repository.
        content (bytes): The content to write.
        object_type (str): The type of the object (blob, tree, commit).

    Returns:
        str: The SHA-1 hash of the object.
    """

    # Prepare the object content with header
    header = f"{object_type} {len(content)}\0".encode()
    store_content = header + content

    # Calculate the SHA-1 hash of the content
    sha1_hash = calculate_sha1_hash(store_content)

    # Compress the content
    compressed_content = compress_content(store_content)

    # Define the object directory
    object_dir = repo_path / ".git" / "objects"

    # Create the object directory if it doesn't exist
    object_subdir = object_dir / sha1_hash[:2]
    object_subdir.mkdir(parents=True, exist_ok=True)
    object_file_path = object_subdir / sha1_hash[2:]

    # Write the compressed content to the object file if it doesn't exist
    if not object_file_path.exists():
        # Write the compressed content to the object file
        with open(object_file_path, "wb") as f:
            f.write(compressed_content)

        # Log the write operation
        logger.debug(f"Wrote {object_type} object file: {object_file_path}")
    else:
        # Log the existence of the object file
        logger.debug(f"Object file already exists: {object_file_path}")

    # Return the SHA-1 hash
    return sha1_hash


# Function to create a blob object
def create_blob_object(repo_path: Path, file_path: Path) -> str:
    """
    Create a blob object for a file.

    Args:
        repo_path (Path): Path to the repository.
        file_path (Path): Path to the file.

    Returns:
        str: The SHA-1 hash of the blob object.
    """

    # Read the file content
    with open(file_path, "rb") as f:
        content = f.read()

    # Write the blob object
    return write_object_file(repo_path, content, "blob")


# Function to create a tree entry
def create_tree_entry(mode: str, name: str, sha1_hash: str) -> bytes:
    """
    Create a tree entry for a file or directory.

    Args:
        mode (str): The file mode (e.g., "100644" for regular file).
        name (str): The name of the file or directory.
        sha1_hash (str): The SHA-1 hash of the blob or tree object.

    Returns:
        bytes: The tree entry as bytes.
    """

    # Convert the SHA-1 hash from hex to binary
    sha1_binary = bytes.fromhex(sha1_hash)

    # Create the tree entry
    return f"{mode} {name}\0".encode() + sha1_binary


# Function to create a tree object
def create_tree_object(
    repo_path: Path, directory_path: Path, ignore_patterns: List[str] = None
) -> str:
    """
    Create a tree object for a directory.

    Args:
        repo_path (Path): Path to the repository.
        directory_path (Path): Path to the directory.
        ignore_patterns (List[str], optional): List of patterns to ignore.
            Defaults to None.

    Returns:
        str: The SHA-1 hash of the tree object.
    """

    # Initialize ignore patterns
    if ignore_patterns is None:
        # Default ignore patterns
        ignore_patterns = [".git"]

    # Initialize tree entries
    entries: List[Tuple[str, str, str]] = []

    # Process all files and directories in the directory
    for item in sorted(os.listdir(directory_path)):
        # Get the item path
        item_path = directory_path / item

        # Skip ignored patterns
        if any(
            pattern in str(item_path.relative_to(repo_path))
            for pattern in ignore_patterns
        ):
            continue

        # Get the file mode
        item_stat = item_path.stat()

        # Check if the item is a file
        if item_path.is_file():
            # Regular file
            mode = "100644"
            if item_stat.st_mode & stat.S_IXUSR:
                # Executable file
                mode = "100755"

            # Create a blob object for the file
            sha1_hash = create_blob_object(repo_path, item_path)

            # Add the entry to the list
            entries.append((mode, item, sha1_hash))

        # Check if the item is a directory
        elif item_path.is_dir():
            # Directory
            mode = "40000"

            # Create a tree object for the subdirectory
            sha1_hash = create_tree_object(repo_path, item_path, ignore_patterns)

            # Add the entry to the list
            entries.append((mode, item, sha1_hash))

    # Create the tree content
    tree_content = b""
    for mode, name, sha1_hash in entries:
        # Create the tree entry
        tree_content += create_tree_entry(mode, name, sha1_hash)

    # Write the tree object
    return write_object_file(repo_path, tree_content, "tree")


# Function to create a commit object
def create_commit_object(
    repo_path: Path,
    tree_hash: str,
    parent_hash: Optional[str],
    author_name: str,
    author_email: str,
    message: str,
) -> str:
    """
    Create a commit object.

    Args:
        repo_path (Path): Path to the repository.
        tree_hash (str): The SHA-1 hash of the root tree object.
        parent_hash (Optional[str]): The SHA-1 hash of the parent commit,
            or None if this is the first commit.
        author_name (str): The name of the author.
        author_email (str): The email of the author.
        message (str): The commit message.

    Returns:
        str: The SHA-1 hash of the commit object.
    """

    # Get the current timestamp
    timestamp = int(time.time())
    timezone = time.strftime("%z")

    # Create the author and committer strings
    author = f"{author_name} <{author_email}> {timestamp} {timezone}"
    committer = author  # Use the same author as committer for simplicity

    # Create the commit content
    commit_content = f"tree {tree_hash}\n"
    if parent_hash:
        commit_content += f"parent {parent_hash}\n"
    commit_content += f"author {author}\n"
    commit_content += f"committer {committer}\n"
    commit_content += f"\n{message}\n"

    # Write the commit object
    return write_object_file(repo_path, commit_content.encode(), "commit")


# Function to parse a tree object
def parse_tree_object(content: bytes) -> List[Tuple[str, str, str, str]]:
    """
    Parse a Git tree object content.

    Args:
        content (bytes): The content of the tree object.

    Returns:
        List[Tuple[str, str, str, str]]: A list of tuples containing:
            - mode (str): The file mode (e.g., "100644" for regular file)
            - type (str): The object type ("blob" or "tree")
            - hash (str): The SHA-1 hash of the object
            - name (str): The name of the file or directory
    """

    # Initialize the entries list
    entries = []

    # Process the content
    i = 0
    while i < len(content):
        # Find the space after the mode
        space_index = content.find(b" ", i)
        if space_index == -1:
            break

        # Extract the mode
        mode = content[i:space_index].decode()

        # Find the null byte after the name
        null_index = content.find(b"\0", space_index + 1)
        if null_index == -1:
            break

        # Extract the name
        name = content[space_index + 1 : null_index].decode()

        # Extract the SHA-1 hash (20 bytes)
        hash_start = null_index + 1
        if hash_start + 20 > len(content):
            break
        sha1_hash = "".join(f"{b:02x}" for b in content[hash_start : hash_start + 20])

        # Determine the object type based on the mode
        obj_type = "tree" if mode.startswith("40") else "blob"

        # Add the entry to the list
        entries.append((mode, obj_type, sha1_hash, name))

        # Move to the next entry
        i = hash_start + 20

    # Return the entries
    return entries
