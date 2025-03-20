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


# Function to create a new branch
def create_branch(
    repo_path: Path, branch_name: str, commit_hash: Optional[str] = None
) -> bool:
    """
    Create a new branch pointing to a commit.

    Args:
        repo_path (Path): Path to the repository.
        branch_name (str): The name of the branch to create.
        commit_hash (Optional[str]): The commit hash to point to. If None, use HEAD.

    Returns:
        bool: True if branch creation was successful, False otherwise.
    """

    # Ensure branch_name does not contain invalid characters
    if "/" in branch_name:
        logger.error(f"Branch name cannot contain '/': {branch_name}")
        return False

    # Define the branch reference path
    branch_ref = f"refs/heads/{branch_name}"
    branch_path = repo_path / ".git" / branch_ref

    # Check if branch already exists
    if branch_path.exists():
        logger.error(f"Branch already exists: {branch_name}")
        return False

    # If no commit_hash provided, use HEAD commit
    if commit_hash is None:
        commit_hash = get_head_commit(repo_path)

        # Check if HEAD commit exists
        if commit_hash is None:
            logger.error("Cannot create branch: HEAD reference is invalid")
            return False

    # Create the branch by updating the reference
    try:
        update_ref(repo_path, branch_ref, commit_hash)
        logger.info(f"Created branch '{branch_name}' pointing to {commit_hash}")
        return True
    except Exception as e:
        logger.error(f"Error creating branch: {str(e)}")
        return False


# Function to list all branches
def list_branches(repo_path: Path) -> list[str]:
    """
    List all branches in the repository.

    Args:
        repo_path (Path): Path to the repository.

    Returns:
        list[str]: A list of branch names.
    """

    # Define the heads directory path
    heads_dir = repo_path / ".git" / "refs" / "heads"

    # Check if the heads directory exists
    if not heads_dir.exists():
        logger.warning("No branches found (refs/heads directory does not exist)")
        return []

    # Get all files in the heads directory (branches)
    branches = []

    # Walk through all files in the heads directory and subdirectories
    for branch_file in heads_dir.glob("**/*"):
        if branch_file.is_file():
            # Get the relative path from the heads directory
            rel_path = branch_file.relative_to(heads_dir)
            # Convert to string path and join with forward slashes
            branch_name = str(rel_path).replace("\\", "/")
            branches.append(branch_name)

    return sorted(branches)


# Function to delete a branch
def delete_branch(repo_path: Path, branch_name: str, force: bool = False) -> bool:
    """
    Delete a branch from the repository.

    Args:
        repo_path (Path): Path to the repository.
        branch_name (str): The name of the branch to delete.
        force (bool): If True, delete the branch even if it's the current branch.

    Returns:
        bool: True if deletion was successful, False otherwise.
    """

    # Get the current branch
    current_branch = get_current_branch(repo_path)

    # Check if attempting to delete the current branch
    if current_branch == branch_name and not force:
        logger.error(f"Cannot delete the current branch: {branch_name}")
        return False

    # Define the branch reference path
    branch_ref_path = repo_path / ".git" / "refs" / "heads" / branch_name

    # Check if branch exists
    if not branch_ref_path.exists():
        logger.error(f"Branch does not exist: {branch_name}")
        return False

    # Delete the branch reference file
    try:
        branch_ref_path.unlink()
        logger.info(f"Deleted branch: {branch_name}")
        return True
    except Exception as e:
        logger.error(f"Error deleting branch: {str(e)}")
        return False
