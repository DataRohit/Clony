"""
Checkout module for Clony.

This module handles the checkout functionality for the Clony Git clone tool,
supporting branch switching, file restoration, and detached HEAD state.
"""

# Standard library imports
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Local imports
from clony.core.diff import read_git_object
from clony.core.objects import parse_tree_object
from clony.core.refs import get_head_commit, get_ref_hash
from clony.internals.reset import (
    update_head_to_commit,
    update_index_to_commit,
    validate_commit_reference,
)
from clony.internals.staging import find_git_repo_path
from clony.internals.status import FileStatus, get_repository_status
from clony.utils.logger import logger

# Initialize rich console for pretty output
console = Console()


# Function to detect conflicts between working directory and target state
def detect_conflicts(
    repo_path: Path, target_commit_hash: str, check_files: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Detect conflicts between uncommitted changes and the target branch/commit.

    This function compares the current working directory state with the target
    branch or commit to identify potential conflicts that would be overwritten
    during checkout.

    Args:
        repo_path (Path): Path to the repository.
        target_commit_hash (str): The commit hash to check against.
        check_files (Optional[List[str]]): Specific files to check. If None,
                                         checks all files.

    Returns:
        Dict[str, str]: Dictionary of conflicting files and the type of conflict.
    """

    # Get repository status
    status_dict = get_repository_status(str(repo_path))

    # Identify modified or deleted files that aren't staged
    modified_files = set(status_dict.get(FileStatus.MODIFIED, []))
    modified_files.update(status_dict.get(FileStatus.BOTH_MODIFIED, []))
    deleted_files = set(status_dict.get(FileStatus.DELETED, []))
    deleted_files.update(status_dict.get(FileStatus.BOTH_DELETED, []))

    # Filter to specific files if provided
    if check_files:
        check_files_set = set(check_files)
        modified_files = modified_files.intersection(check_files_set)
        deleted_files = deleted_files.intersection(check_files_set)

    # Read the tree from the target commit
    target_tree_hash = get_commit_tree_hash(repo_path, target_commit_hash)
    if not target_tree_hash:
        logger.error(f"Failed to get tree hash for commit {target_commit_hash}")
        return {}

    # Get target files state
    target_files = get_files_from_tree(repo_path, target_tree_hash)

    # Check for conflicts
    conflicts = {}

    # Files that would be overwritten
    for file_path in modified_files:
        if file_path in target_files:
            conflicts[file_path] = "modified"

    # Files that exist in target but are deleted locally
    for file_path in deleted_files:
        if file_path in target_files:
            conflicts[file_path] = "deleted"

    # Return the conflicts
    return conflicts


# Function to get tree hash from commit
def get_commit_tree_hash(repo_path: Path, commit_hash: str) -> Optional[str]:
    """
    Get the tree hash from a commit object.

    Args:
        repo_path (Path): Path to the repository.
        commit_hash (str): The commit hash.

    Returns:
        Optional[str]: The tree hash, or None if not found.
    """

    try:
        # Read the commit object
        obj_type, content = read_git_object(repo_path, commit_hash)

        # Ensure it's a commit object
        if obj_type != "commit":
            logger.error(f"Object {commit_hash} is not a commit")
            return None

        # Parse the commit content to get the tree hash
        lines = content.decode("utf-8").split("\n")
        for line in lines:
            if line.startswith("tree "):
                return line[5:].strip()

        # Log the error
        logger.error(f"Tree hash not found in commit {commit_hash}")
        return None

    except Exception as e:
        # Log the error
        logger.error(f"Failed to read commit object: {str(e)}")
        return None


# Function to get files from a tree
def get_files_from_tree(
    repo_path: Path, tree_hash: str, prefix: str = ""
) -> Dict[str, str]:
    """
    Get all files and their hashes from a tree object.

    Args:
        repo_path (Path): Path to the repository.
        tree_hash (str): The tree hash.
        prefix (str): Path prefix for recursive calls.

    Returns:
        Dict[str, str]: Dictionary mapping file paths to their object hashes.
    """

    # Initialize the files dictionary
    files = {}

    try:
        # Read the tree object
        obj_type, content = read_git_object(repo_path, tree_hash)

        # Ensure it's a tree object
        if obj_type != "tree":
            logger.error(f"Object {tree_hash} is not a tree")
            return {}

        # Parse the tree object
        tree_entries = parse_tree_object(content)

        # Process each entry in the tree
        for entry in tree_entries:
            mode, obj_type, obj_hash, name = entry
            path = f"{prefix}{name}" if prefix else name

            # If it's a blob (file), add it to the result
            if mode.startswith("100"):  # Regular file
                files[path] = obj_hash

            # If it's a tree (directory), recursively process it
            elif mode == "40000":  # Directory
                subfiles = get_files_from_tree(repo_path, obj_hash, f"{path}/")
                files.update(subfiles)

        # Return the files
        return files

    except Exception as e:
        # Log the error
        logger.error(f"Failed to process tree {tree_hash}: {str(e)}")
        return {}


# Function to extract blob content to working directory
def extract_blob_to_working_dir(
    repo_path: Path, blob_hash: str, file_path: str
) -> bool:
    """
    Extract a blob object to the working directory.

    Args:
        repo_path (Path): Path to the repository.
        blob_hash (str): The blob object hash.
        file_path (str): The path to write the file to.

    Returns:
        bool: True if successful, False otherwise.
    """

    try:
        # Read the blob object
        obj_type, content = read_git_object(repo_path, blob_hash)

        # Ensure it's a blob object
        if obj_type != "blob":
            logger.error(f"Object {blob_hash} is not a blob")
            return False

        # Create directory structure if needed
        full_path = repo_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the content to the file
        with open(full_path, "wb") as f:
            f.write(content)

        # Log the success
        logger.debug(f"Extracted blob {blob_hash} to {file_path}")
        return True

    except Exception as e:
        # Log the error
        logger.error(f"Failed to extract blob {blob_hash} to {file_path}: {str(e)}")
        return False


# Function to update the working directory to match a tree
def update_working_dir_to_tree(
    repo_path: Path, tree_hash: str, specific_files: Optional[List[str]] = None
) -> bool:
    """
    Update the working directory to match a tree object.

    Args:
        repo_path (Path): Path to the repository.
        tree_hash (str): The tree hash.
        specific_files (Optional[List[str]]): Specific files to update. If None,
                                             updates all files.

    Returns:
        bool: True if successful, False otherwise.
    """

    try:
        # Get the files from the tree
        files = get_files_from_tree(repo_path, tree_hash)
        if not files:
            return False

        # If specific files are requested, filter the files
        if specific_files:
            files = {k: v for k, v in files.items() if k in specific_files}

        # Extract each file
        for file_path, blob_hash in files.items():
            # Extract the blob to the working directory
            success = extract_blob_to_working_dir(repo_path, blob_hash, file_path)
            if not success:
                # Log the error
                logger.error(f"Failed to update file {file_path}")
                return False

        # Log the success
        return True

    except Exception as e:
        # Log the error
        logger.error(f"Failed to update working directory: {str(e)}")
        return False


# Function to restore specific files from a commit
def restore_specific_files(
    repo_path: Path, commit_hash: str, file_paths: List[str]
) -> bool:
    """
    Restore specific files from a commit.

    Args:
        repo_path (Path): Path to the repository.
        commit_hash (str): The commit hash.
        file_paths (List[str]): List of file paths to restore.

    Returns:
        bool: True if successful, False otherwise.
    """

    # Get the tree hash from the commit
    logger.debug(f"Getting tree hash for commit {commit_hash}")
    tree_hash = get_commit_tree_hash(repo_path, commit_hash)
    if not tree_hash:
        logger.error(f"Failed to get tree hash for commit {commit_hash}")
        return False

    # Update the working directory with the specified files
    logger.debug(
        f"Updating working directory for {len(file_paths)} files from tree {tree_hash}"
    )
    return update_working_dir_to_tree(repo_path, tree_hash, file_paths)


# Function to display checkout information
def display_checkout_info(
    target_ref: str, is_branch: bool, is_detached: bool, files_updated: int
) -> None:
    """
    Display checkout information in a formatted table.

    Args:
        target_ref (str): The branch or commit that was checked out.
        is_branch (bool): Whether the target is a branch.
        is_detached (bool): Whether HEAD is now in a detached state.
        files_updated (int): Number of files updated.
    """

    # Create a table for displaying checkout information
    table = Table(title="Checkout Results")

    # Add columns
    table.add_column("Target", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("HEAD State", style="green")
    table.add_column("Files Updated", style="magenta")

    # Determine the type
    ref_type = "Branch" if is_branch else "Commit"

    # Determine HEAD state
    head_state = "Detached" if is_detached else "Attached"

    # Add the row
    table.add_row(target_ref, ref_type, head_state, str(files_updated))

    # Display the table
    console.print(table)

    # Add warning for detached HEAD
    if is_detached:
        warning = Text()
        warning.append("\nYou are in 'detached HEAD' state. You can look around, make ")
        warning.append("experimental changes and commit them, and you can discard any ")
        warning.append("commits you make in this state without impacting any branches ")
        warning.append("by switching back to a branch.\n\n")
        warning.append(
            "If you want to create a new branch to retain commits you create, you can "
        )
        warning.append("do so (now or later) by using:\n\n")
        warning.append("  clony branch <new-branch-name>\n", style="bold cyan")

        # Create a panel for the logo
        warning_panel = Panel(
            warning,
            title="[bold yellow]Warning: Detached HEAD[/bold yellow]",
            border_style="yellow",
        )
        console.print(warning_panel)


# Function to display conflicts
def display_conflicts(conflicts: Dict[str, str]) -> None:
    """
    Display checkout conflicts in a formatted table.

    Args:
        conflicts (Dict[str, str]): Dictionary of conflicting files and conflict types.
    """

    # Create a table for displaying conflicts
    table = Table(title="Checkout Conflicts")

    # Add columns
    table.add_column("File", style="cyan")
    table.add_column("Status", style="red")
    table.add_column("Action Required", style="yellow")

    # Add rows for each conflict
    for file_path, conflict_type in conflicts.items():
        if conflict_type == "modified":
            action = "Commit or stash changes"
        else:  # deleted
            action = "Restore or commit deletion"

        table.add_row(file_path, conflict_type.capitalize(), action)

    # Display the table
    console.print(table)

    # Add helpful message
    help_text = Text()
    help_text.append(
        "\nYour local changes to the above files would be overwritten by checkout.\n"
    )
    help_text.append(
        "Please commit your changes or stash them before you switch branches.\n"
    )

    help_panel = Panel(
        help_text,
        title="[bold red]Error: Cannot Checkout[/bold red]",
        border_style="red",
    )
    console.print(help_panel)


# Function to switch to a branch or commit
def switch_branch_or_commit(
    target_ref: str, force: bool = False, repo_path: Optional[Path] = None
) -> bool:
    """
    Switch to a branch or commit (checkout).

    This function updates HEAD, the index, and the working directory to
    reflect the state of the target branch or commit.

    Args:
        target_ref (str): The branch or commit to check out.
        force (bool): Whether to force the checkout, overwriting changes.
        repo_path (Optional[Path]): Path to the repository. If None, the current
                                  directory is used.

    Returns:
        bool: True if successful, False otherwise.
    """

    # Find the Git repository path if not provided
    if repo_path is None:
        repo_path = find_git_repo_path(Path.cwd())

    # If not in a Git repository
    if not repo_path:
        # Log the error
        logger.error("Not in a Git repository")
        return False

    # Check if target is a branch
    branch_ref = f"refs/heads/{target_ref}"
    is_branch = False
    commit_hash = None

    # Try to get the commit hash for the branch
    branch_hash = get_ref_hash(repo_path, branch_ref)
    if branch_hash:
        is_branch = True
        commit_hash = branch_hash
    else:
        # If not a branch, validate as a commit reference
        commit_hash = validate_commit_reference(repo_path, target_ref)

    if not commit_hash:
        logger.error(f"Invalid reference: {target_ref}")
        return False

    # Check for conflicts unless forcing
    if not force:
        conflicts = detect_conflicts(repo_path, commit_hash)
        if conflicts:
            display_conflicts(conflicts)
            return False

    # Get tree hash from commit
    tree_hash = get_commit_tree_hash(repo_path, commit_hash)
    if not tree_hash:
        logger.error(f"Failed to get tree hash for commit {commit_hash}")
        return False

    # Get files to be updated
    files_to_update = get_files_from_tree(repo_path, tree_hash)
    files_count = len(files_to_update)

    # Update HEAD
    if is_branch:
        # Point HEAD to the branch reference
        head_file = repo_path / ".git" / "HEAD"
        with open(head_file, "w") as f:
            f.write(f"ref: {branch_ref}\n")
        logger.debug(f"Updated HEAD to reference {branch_ref}")
        is_detached = False
    else:
        # Update HEAD to point directly to the commit (detached HEAD)
        if not update_head_to_commit(repo_path, commit_hash):
            logger.error(f"Failed to update HEAD to {commit_hash}")
            return False
        is_detached = True

    # Update index
    if not update_index_to_commit(repo_path, commit_hash):
        logger.error("Failed to update index")
        return False

    # Update working directory
    if not update_working_dir_to_tree(repo_path, tree_hash):
        logger.error("Failed to update working directory")
        return False

    # Display checkout information
    display_checkout_info(target_ref, is_branch, is_detached, files_count)

    # Log the success
    return True


# Function to restore files from a specific commit
def restore_files(
    paths: List[str],
    source_ref: str = "HEAD",
    repo_path: Optional[Path] = None,
    force: bool = False,
) -> bool:
    """
    Restore specified files from a reference (branch, commit).

    This function updates the specified files in the working directory to
    their versions in the target reference.

    Args:
        paths (List[str]): Paths of files to restore.
        source_ref (str): Reference to restore from. Defaults to HEAD.
        repo_path (Optional[Path]): Path to the repository. If None, the current
                                  directory is used.
        force (bool): Whether to force the restore, overwriting uncommitted changes.

    Returns:
        bool: True if successful, False otherwise.
    """

    # Find the Git repository path if not provided
    if repo_path is None:
        repo_path = find_git_repo_path(Path.cwd())

    if not repo_path:
        logger.error("Not in a Git repository")
        return False

    # Resolve the source reference to a commit hash
    if source_ref == "HEAD":
        commit_hash = get_head_commit(repo_path)
        if not commit_hash:
            logger.error("Failed to get HEAD commit")
            return False
    else:
        # Check if source is a branch
        branch_ref = f"refs/heads/{source_ref}"
        branch_hash = get_ref_hash(repo_path, branch_ref)

        if branch_hash:
            # It's a branch
            commit_hash = branch_hash
        else:
            # Validate as a commit reference
            commit_hash = validate_commit_reference(repo_path, source_ref)

    if not commit_hash:
        logger.error(f"Invalid reference: {source_ref}")
        return False

    # Check for conflicts in the specified files, unless force is specified
    if not force:
        conflicts = detect_conflicts(repo_path, commit_hash, paths)
        if conflicts:
            display_conflicts(conflicts)
            return False

    # Restore the files
    if not restore_specific_files(repo_path, commit_hash, paths):
        logger.error(f"Failed to restore files from {source_ref}")
        return False

    # Display success message
    logger.error(f"Restored {len(paths)} file(s) from {source_ref}")

    # Log the success
    return True
