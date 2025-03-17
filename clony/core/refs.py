"""
Git references functionality for Clony.

This module provides the core functionality for Git references, including HEAD
and branches.
"""

# Standard library imports
from pathlib import Path
from typing import Optional

# Local imports
from clony.utils.logger import logger


# Function to get the current HEAD reference
def get_head_ref(repo_path: Path) -> str:
    """
    Get the current HEAD reference.

    Args:
        repo_path (Path): Path to the repository.

    Returns:
        str: The current HEAD reference (e.g., "refs/heads/main").
    """

    # Define the HEAD file path
    head_file = repo_path / ".git" / "HEAD"

    # Read the HEAD file
    with open(head_file, "r") as f:
        head_content = f.read().strip()

    # Check if HEAD is a reference or a direct commit hash
    if head_content.startswith("ref: "):
        # Return the reference
        return head_content[5:]
    else:
        # Return the commit hash
        return head_content


# Function to get the current branch name
def get_current_branch(repo_path: Path) -> Optional[str]:
    """
    Get the current branch name.

    Args:
        repo_path (Path): Path to the repository.

    Returns:
        Optional[str]: The current branch name, or None if HEAD is detached.
    """

    # Get the HEAD reference
    head_ref = get_head_ref(repo_path)

    # Check if HEAD is a branch reference
    if head_ref.startswith("refs/heads/"):
        # Return the branch name
        return head_ref[11:]
    else:
        # HEAD is detached
        return None


# Function to update a reference
def update_ref(repo_path: Path, ref_name: str, commit_hash: str) -> None:
    """
    Update a reference to point to a commit.

    Args:
        repo_path (Path): Path to the repository.
        ref_name (str): The name of the reference (e.g., "refs/heads/main").
        commit_hash (str): The commit hash to point to.
    """

    # Define the reference file path
    ref_file = repo_path / ".git" / ref_name

    # Create the parent directory if it doesn't exist
    ref_file.parent.mkdir(parents=True, exist_ok=True)

    # Write the commit hash to the reference file
    with open(ref_file, "w") as f:
        f.write(commit_hash + "\n")

    logger.debug(f"Updated reference {ref_name} to {commit_hash}")


# Function to get the commit hash for a reference
def get_ref_hash(repo_path: Path, ref_name: str) -> Optional[str]:
    """
    Get the commit hash for a reference.

    Args:
        repo_path (Path): Path to the repository.
        ref_name (str): The name of the reference (e.g., "refs/heads/main").

    Returns:
        Optional[str]: The commit hash, or None if the reference doesn't exist.
    """

    # Define the reference file path
    ref_file = repo_path / ".git" / ref_name

    # Check if the reference file exists
    if not ref_file.exists():
        return None

    # Read the reference file
    with open(ref_file, "r") as f:
        return f.read().strip()


# Function to get the commit hash for HEAD
def get_head_commit(repo_path: Path) -> Optional[str]:
    """
    Get the commit hash for HEAD.

    Args:
        repo_path (Path): Path to the repository.

    Returns:
        Optional[str]: The commit hash for HEAD, or None if HEAD doesn't exist
        or points to a non-existent reference.
    """

    # Get the HEAD reference
    head_ref = get_head_ref(repo_path)

    # Check if HEAD is a reference or a direct commit hash
    if head_ref.startswith("refs/"):
        # Get the commit hash for the reference
        return get_ref_hash(repo_path, head_ref)
    else:
        # HEAD is a direct commit hash
        return head_ref
