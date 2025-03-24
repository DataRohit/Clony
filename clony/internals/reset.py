"""
Reset module for Clony.

This module handles the reset functionality for the Clony Git clone tool,
supporting soft, mixed, and hard reset modes.
"""

# Standard library imports
from pathlib import Path
from typing import Dict, Literal, Optional

# Third-party imports
from rich.console import Console
from rich.table import Table

# Local imports
from clony.core.refs import get_head_ref, get_ref_hash, update_ref
from clony.internals.log import parse_commit_object, read_git_object
from clony.internals.staging import clear_staging_area, find_git_repo_path
from clony.utils.logger import logger

# Initialize rich console for pretty output
console = Console()


# Function to validate commit hash or reference
def validate_commit_reference(repo_path: Path, commit_ref: str) -> Optional[str]:
    """
    Validate and resolve a commit reference to a commit hash.

    This function takes a commit reference (hash, branch, or tag) and attempts
    to resolve it to a full commit hash, verifying that it exists in the repository.

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

    This function updates the HEAD reference to point to the specified commit,
    handling both regular references and detached HEAD states.

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

    This function clears the current index (staging area) to match the state
    at the specified commit.

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

    This function updates the working directory files to match their state
    at the specified commit.

    Args:
        repo_path (Path): Path to the repository.
        commit_hash (str): The commit hash to match.

    Returns:
        bool: True if successful, False otherwise.
    """

    try:
        import os
        import shutil

        # Import here to avoid circular imports
        from clony.internals.checkout import (
            get_commit_tree_hash,
            get_files_from_tree,
            update_working_dir_to_tree,
        )

        # Get the tree hash from the commit
        tree_hash = get_commit_tree_hash(repo_path, commit_hash)
        if not tree_hash:
            logger.error(f"Failed to get tree hash for commit {commit_hash}")
            return False

        # Get the files from the target tree
        target_files = get_files_from_tree(repo_path, tree_hash)

        # Walk the working directory to identify files that should be removed
        git_dir = repo_path / ".git"

        # First remove unwanted files
        for root, _, files in os.walk(repo_path):
            root_path = Path(root)

            # Skip the .git directory
            if git_dir in root_path.parents or root_path == git_dir:
                continue

            # Process files in the current directory
            for file in files:
                file_path = root_path / file
                relative_path = file_path.relative_to(repo_path)
                # Ensure consistent path separators
                rel_path_str = str(relative_path).replace("\\", "/")

                # If the file doesn't exist in the target tree, remove it
                if rel_path_str not in target_files:
                    try:
                        file_path.unlink()
                        logger.debug(f"Removed file: {rel_path_str}")
                    except Exception as e:
                        logger.warning(
                            f"Failed to remove file {rel_path_str}: {str(e)}"
                        )

        # Now handle directories
        # Get all directories in the working directory
        all_dirs = []
        for root, dirs, _ in os.walk(repo_path):
            root_path = Path(root)
            if git_dir in root_path.parents or root_path == git_dir:
                continue

            for dir_name in dirs:
                dir_path = root_path / dir_name
                if git_dir not in dir_path.parents and dir_path != git_dir:
                    all_dirs.append(dir_path)

        # Sort directories by depth (deepest first)
        all_dirs.sort(key=lambda p: len(p.parts), reverse=True)

        # Remove empty directories
        for dir_path in all_dirs:
            try:
                # Check if directory exists and is empty
                if dir_path.exists() and not any(dir_path.iterdir()):
                    shutil.rmtree(dir_path)
                    rel_path = dir_path.relative_to(repo_path)
                    logger.debug(f"Removed directory: {rel_path}")
            except Exception as e:
                rel_path = dir_path.relative_to(repo_path)
                logger.warning(f"Failed to remove directory {rel_path}: {str(e)}")

        # Update the working directory to match the tree
        if not update_working_dir_to_tree(repo_path, tree_hash):
            logger.error(
                f"Failed to update working directory to match tree {tree_hash}"
            )
            return False

        # Log the update
        logger.debug(f"Updated working directory to match commit {commit_hash}")

        # Return True to indicate success
        return True
    except Exception as e:
        # Log any unexpected errors
        logger.error(f"Failed to update working directory: {str(e)}")
        return False


# Function to display reset information in a table
def display_reset_info(
    commit_hash: str, mode: str, commit_info: Optional[Dict[str, str]] = None
) -> None:
    """
    Display reset information in a formatted table.

    This function creates and displays a formatted table showing details of
    the reset operation, including commit information if available.

    Args:
        commit_hash (str): The hash of the commit HEAD was reset to.
        mode (str): The reset mode (soft, mixed, or hard).
        commit_info (Optional[Dict[str, str]]): Optional commit information.
    """
    # Create a table for displaying reset information
    table = Table(title="Reset Results")

    # Add columns to the table
    table.add_column("Commit Hash", style="cyan")
    table.add_column("Reset Mode", style="yellow")
    table.add_column("Actions Taken", style="green")

    # Define actions based on mode
    actions = []
    if mode == "soft":
        actions.append("HEAD pointer updated")
    elif mode == "mixed":
        actions.append("HEAD pointer updated")
        actions.append("Index/staging area reset")
    elif mode == "hard":
        actions.append("HEAD pointer updated")
        actions.append("Index/staging area reset")
        actions.append("Working directory reset")

    # Format actions as a list
    actions_text = "\n".join([f"• {action}" for action in actions])

    # Add the reset information to the table
    table.add_row(commit_hash[:8], mode.upper(), actions_text)

    # Display the reset information table
    console.print(table)

    # If commit info is provided, display it in a separate table
    if commit_info:
        # Create a table for displaying commit information
        commit_table = Table(title="Commit Details")

        # Add columns to the table
        commit_table.add_column("Property", style="yellow")
        commit_table.add_column("Value", style="white")

        # Add commit information rows
        for key, value in commit_info.items():
            if key == "message":
                # Truncate long messages
                if len(value) > 50:
                    value = value[:47] + "..."
            commit_table.add_row(key.capitalize(), value)

        # Display the commit information table
        console.print(commit_table)


# Main reset function
def reset_head(
    commit_ref: str,
    mode: Literal["soft", "mixed", "hard"] = "mixed",
    repo_path: Optional[Path] = None,
) -> bool:
    """
    Reset HEAD to a specific commit with different modes.

    This function resets the HEAD reference to point to a specific commit,
    with options to also update the index and working directory.

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

    # Try to get commit information for display
    commit_info = None
    try:
        object_type, content = read_git_object(repo_path, commit_hash)
        if object_type == "commit":
            commit_info = parse_commit_object(content)
    except Exception as e:
        # If we can't get commit info, just proceed without it
        logger.debug(f"Failed to read commit info: {str(e)}")

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

    # Display reset information in a table
    display_reset_info(commit_hash, mode, commit_info)

    # Return True to indicate success
    return True

    # Return True to indicate success
    return True
    return True

    # Return True to indicate success
    return True
    return True

    # Return True to indicate success
    return True

    # Return True to indicate success
    return True
    return True

    # Return True to indicate success
    return True
