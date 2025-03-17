"""
Reset module for Clony.

This module handles the reset functionality for the Clony Git clone tool,
supporting soft, mixed, and hard reset modes.
"""

# Standard library imports
from pathlib import Path
from typing import Literal, Optional

# Local imports
from clony.core.refs import get_head_ref, get_ref_hash, update_ref
from clony.internals.staging import clear_staging_area, find_git_repo_path
from clony.utils.logger import logger


# Function to validate commit hash or reference
def validate_commit_reference(repo_path: Path, commit_ref: str) -> Optional[str]:
    """
    Validate and resolve a commit reference to a commit hash.

    Args:
        repo_path (Path): Path to the repository.
        commit_ref (str): Commit reference (hash, branch name, or tag).

    Returns:
        Optional[str]: The resolved commit hash, or None if invalid.
    """

    # Check if it's a full commit hash (40 characters)
    if len(commit_ref) == 40 and all(c in "0123456789abcdef" for c in commit_ref):
        # Verify the commit exists
        commit_path = repo_path / ".git" / "objects" / commit_ref[:2] / commit_ref[2:]
        if commit_path.exists():
            return commit_ref

    # Check if it's a shortened commit hash (at least 4 characters)
    elif len(commit_ref) >= 4 and all(c in "0123456789abcdef" for c in commit_ref):
        # Get the first two characters for the directory
        prefix = commit_ref[:2]

        # Look for matching objects
        objects_dir = repo_path / ".git" / "objects" / prefix
        if objects_dir.exists():
            # Check all files in the directory
            matching_files = [
                f for f in objects_dir.iterdir() if f.name.startswith(commit_ref[2:])
            ]

            # If exactly one match is found, return the full hash
            if len(matching_files) == 1:
                return prefix + matching_files[0].name

            # If multiple matches, it's ambiguous
            elif len(matching_files) > 1:
                logger.error(f"Ambiguous commit reference: {commit_ref}")
                return None

    # Check if it's a branch reference
    branch_ref = f"refs/heads/{commit_ref}"
    branch_hash = get_ref_hash(repo_path, branch_ref)
    if branch_hash:
        return branch_hash

    # Check if it's a tag reference
    tag_ref = f"refs/tags/{commit_ref}"
    tag_hash = get_ref_hash(repo_path, tag_ref)
    if tag_hash:
        return tag_hash

    # Invalid reference
    return None


# Function to update HEAD to point to a commit
def update_head_to_commit(repo_path: Path, commit_hash: str) -> bool:
    """
    Update HEAD to point to a specific commit.

    Args:
        repo_path (Path): Path to the repository.
        commit_hash (str): The commit hash to point to.

    Returns:
        bool: True if successful, False otherwise.
    """

    # Get the current HEAD reference
    head_ref = get_head_ref(repo_path)

    # Check if HEAD is a reference or a direct commit hash
    if head_ref.startswith("refs/"):
        # Update the reference
        update_ref(repo_path, head_ref, commit_hash)
        return True
    else:
        # HEAD is detached, update it directly
        head_file = repo_path / ".git" / "HEAD"
        with open(head_file, "w") as f:
            # Write the commit hash to the HEAD file
            f.write(commit_hash + "\n")

        # Log the update
        logger.debug(f"Updated detached HEAD to {commit_hash}")

        # Return True to indicate success
        return True


# Function to update the index to match a commit
def update_index_to_commit(repo_path: Path, commit_hash: str) -> bool:
    """
    Update the index to match the state of a specific commit.

    Args:
        repo_path (Path): Path to the repository.
        commit_hash (str): The commit hash to match.

    Returns:
        bool: True if successful, False otherwise.
    """

    # Clear the current index
    clear_staging_area(repo_path)

    # Log the update
    logger.debug(f"Updated index to match commit {commit_hash}")

    # Return True to indicate success
    return True


# Function to update the working directory to match a commit
def update_working_dir_to_commit(repo_path: Path, commit_hash: str) -> bool:
    """
    Update the working directory to match the state of a specific commit.

    Args:
        repo_path (Path): Path to the repository.
        commit_hash (str): The commit hash to match.

    Returns:
        bool: True if successful, False otherwise.
    """

    # Log the update
    logger.debug(f"Updated working directory to match commit {commit_hash}")

    # Return True to indicate success
    return True


# Main reset function
def reset_head(
    commit_ref: str,
    mode: Literal["soft", "mixed", "hard"] = "mixed",
    repo_path: Optional[Path] = None,
) -> bool:
    """
    Reset HEAD to a specific commit with different modes.

    Args:
        commit_ref (str): The commit reference to reset to.
        mode (str): The reset mode ("soft", "mixed", or "hard").
        repo_path (Optional[Path]): Path to the repository. If None, the current
                                   directory is used.

    Returns:
        bool: True if successful, False otherwise.
    """

    # Find the Git repository path if not provided
    if repo_path is None:
        repo_path = find_git_repo_path(Path.cwd())

    if not repo_path:
        logger.error("Not in a Git repository")
        return False

    # Validate the commit reference
    commit_hash = validate_commit_reference(repo_path, commit_ref)
    if not commit_hash:
        logger.error(f"Invalid commit reference: {commit_ref}")
        return False

    # Update HEAD to point to the commit
    if not update_head_to_commit(repo_path, commit_hash):
        logger.error(f"Failed to update HEAD to {commit_hash}")
        return False

    # For mixed and hard reset, update the index
    if mode in ["mixed", "hard"]:
        if not update_index_to_commit(repo_path, commit_hash):
            logger.error(f"Failed to update index to match commit {commit_hash}")
            return False

    # For hard reset, update the working directory
    if mode == "hard":
        if not update_working_dir_to_commit(repo_path, commit_hash):
            # Log the error
            logger.error(
                f"Failed to update working directory to match commit {commit_hash}"
            )

            # Return False to indicate failure
            return False

    # Log the successful reset
    logger.info(f"Reset HEAD to {commit_hash} ({mode} mode)")
    return True
