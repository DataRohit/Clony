"""
Status module for Clony.

This module provides functionality to check the status of files in a Git repository,
including whether files are staged, modified, untracked, deleted, etc.
"""

# Standard library imports
import os
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Third-party imports
try:  # pragma: no cover
    import colorama
    from colorama import Fore, Style

    colorama.init(autoreset=False)
    COLOR_SUPPORT = True
except ImportError:  # pragma: no cover
    COLOR_SUPPORT = False

# Rich imports for tabular display
from rich.console import Console
from rich.table import Table

# Local imports
from clony.core.objects import calculate_sha1_hash
from clony.core.refs import get_head_commit
from clony.internals.commit import read_index_file
from clony.internals.staging import find_git_repo_path
from clony.utils.logger import logger

# Initialize console for Rich
console = Console()


# File status enum
class FileStatus(Enum):
    """Enum representing the status of a file in the repository."""

    UNMODIFIED = auto()  # File is tracked and unchanged
    MODIFIED = auto()  # File is tracked and modified but not staged
    STAGED_NEW = auto()  # New file that has been staged
    STAGED_MODIFIED = auto()  # Modified file that has been staged
    STAGED_DELETED = auto()  # File that has been deleted and the deletion is staged
    UNTRACKED = auto()  # File is not tracked
    DELETED = auto()  # File was tracked but has been deleted (not staged)
    BOTH_MODIFIED = auto()  # File is staged but then modified again
    BOTH_DELETED = auto()  # File is staged but then deleted


# Get the content hash of a file
def get_file_content_hash(file_path: Path) -> str:
    """
    Calculate the SHA-1 hash of a file's content.

    Args:
        file_path (Path): Path to the file.

    Returns:
        str: SHA-1 hash of the file content, or empty string if file doesn't exist.
    """

    try:
        # Check if file exists and is a file
        if not file_path.exists() or not file_path.is_file():
            return ""

        # Read the file content
        with open(file_path, "rb") as f:
            content = f.read()

        # Calculate the hash of the file content
        return calculate_sha1_hash(content)

    except Exception as e:
        # Log the error
        logger.error(f"Error calculating hash for {file_path}: {str(e)}")
        return ""


# Get the file tree from a commit
def get_commit_tree(repo_path: Path, commit_hash: str) -> Dict[str, str]:
    """
    Get the file tree from a commit.

    Args:
        repo_path (Path): Path to the repository.
        commit_hash (str): Hash of the commit.

    Returns:
        Dict[str, str]: Dictionary mapping file paths to their SHA-1 hashes.
    """

    # Return empty dict if no commit hash
    if not commit_hash:
        return {}

    try:
        # First check if HEAD_TREE file exists, which is our simplified approach
        head_tree_file = repo_path / ".git" / "HEAD_TREE"
        if head_tree_file.exists():
            try:
                return read_index_file(head_tree_file)
            except Exception as e:
                logger.error(f"Error reading HEAD_TREE file: {str(e)}")

        # Define the commit object path
        commit_dir = repo_path / ".git" / "objects" / commit_hash[:2]
        commit_file = commit_dir / commit_hash[2:]

        # Check if commit object exists
        if not commit_file.exists():
            logger.error(f"Commit object not found: {commit_hash}")
            return {}

        # If we get here, we couldn't read the commit tree
        return {}

    except Exception as e:
        # Log the error
        logger.error(f"Error reading commit tree: {str(e)}")
        return {}


# Get the tracked files from the last commit
def get_tracked_files(repo_path: Path) -> Dict[str, str]:
    """
    Get all tracked files from the last commit.

    Args:
        repo_path (Path): Path to the repository.

    Returns:
        Dict[str, str]: Dictionary mapping file paths to their SHA-1 hashes.
    """

    # Get the head commit
    head_commit = get_head_commit(repo_path)

    # Get the file tree from the head commit
    return get_commit_tree(repo_path, head_commit)


# Get the staged files from the index
def get_staged_files(repo_path: Path) -> Dict[str, str]:
    """
    Get all staged files from the index.

    Args:
        repo_path (Path): Path to the repository.

    Returns:
        Dict[str, str]: Dictionary mapping file paths to their SHA-1 hashes.
    """

    # Get the index file
    index_file = repo_path / ".git" / "index"

    # Return the index file
    return read_index_file(index_file)


# Get all files in the repository (excluding .git directory)
def get_all_files(repo_path: Path) -> Set[str]:
    """
    Get all files in the repository (excluding .git directory).

    Args:
        repo_path (Path): Path to the repository.

    Returns:
        Set[str]: Set of file paths.
    """

    # Initialize the set of files
    all_files = set()

    # Walk through the repository
    for root, _, files in os.walk(repo_path):
        root_path = Path(root)

        # Skip .git directory
        if ".git" in root_path.parts:
            continue

        for file in files:
            # Get the file path
            file_path = root_path / file

            # Convert to relative path from repo root
            rel_path = str(file_path.relative_to(repo_path))

            # Add the file to the set
            all_files.add(rel_path)

    # Return the set of files
    return all_files


# Get the status of a file
def get_file_status(
    file_path: str,
    repo_path: Path,
    tracked_files: Dict[str, str],
    staged_files: Dict[str, str],
    working_dir_files: Set[str],
) -> FileStatus:
    """
    Determine the status of a file.

    Args:
        file_path (str): Path to the file relative to the repository root.
        repo_path (Path): Path to the repository.
        tracked_files (Dict[str, str]): Dictionary of tracked files and their hashes.
        staged_files (Dict[str, str]): Dictionary of staged files and their hashes.
        working_dir_files (Set[str]): Set of files in the working directory.

    Returns:
        FileStatus: Status of the file.
    """

    # Check if the file exists in the working directory
    file_exists = file_path in working_dir_files

    # Check if the file is tracked
    file_tracked = file_path in tracked_files

    # Check if the file is staged
    file_staged = file_path in staged_files

    # File is not tracked and not staged
    if not file_tracked and not file_staged and file_exists:
        return FileStatus.UNTRACKED

    # File was tracked but has been deleted (not staged)
    if file_tracked and not file_staged and not file_exists:
        return FileStatus.DELETED

    # File is staged as a new file
    if not file_tracked and file_staged and file_exists:
        # Check if the file has been modified after staging
        staged_hash = staged_files[file_path]
        current_hash = get_file_content_hash(repo_path / file_path)

        if current_hash != staged_hash:
            return FileStatus.BOTH_MODIFIED

        return FileStatus.STAGED_NEW

    # File is staged for deletion
    if file_tracked and file_staged and not file_exists:
        return FileStatus.STAGED_DELETED

    # File is staged but then deleted
    if file_staged and not file_exists:
        return FileStatus.BOTH_DELETED

    # File is tracked and exists
    if file_tracked and file_exists:
        tracked_hash = tracked_files[file_path]
        current_hash = get_file_content_hash(repo_path / file_path)

        # File is modified but not staged
        if current_hash != tracked_hash and not file_staged:
            return FileStatus.MODIFIED

        # File is staged
        if file_staged:
            staged_hash = staged_files[file_path]

            # File is staged but then modified again
            if current_hash != staged_hash:
                return FileStatus.BOTH_MODIFIED

            # File is staged with modifications
            if staged_hash != tracked_hash:
                return FileStatus.STAGED_MODIFIED

    # Default: file is unmodified
    return FileStatus.UNMODIFIED


# Get the status of all files in the repository
def get_repository_status(repo_path_str: str) -> Dict[FileStatus, List[str]]:
    """
    Get the status of all files in the repository.

    Args:
        repo_path_str (str): Path to the repository.

    Returns:
        Dict[FileStatus, List[str]]: Dictionary mapping file statuses to lists of
        file paths.
    """

    try:
        # Convert to Path object
        path = Path(repo_path_str)

        # Find git repository
        repo_path = find_git_repo_path(path)
        if not repo_path:
            logger.error("Not a git repository. Run 'clony init' to create one.")
            return {}

        # Get tracked files from the last commit
        tracked_files = get_tracked_files(repo_path)

        # Get staged files from the index
        staged_files = get_staged_files(repo_path)

        # Get all files in the working directory
        working_dir_files = get_all_files(repo_path)

        # Combine all file paths
        all_file_paths = (
            set(tracked_files.keys()) | set(staged_files.keys()) | working_dir_files
        )

        # Initialize result dictionary
        status_dict = {status: [] for status in FileStatus}

        # Check status of each file
        for file_path in all_file_paths:
            status = get_file_status(
                file_path, repo_path, tracked_files, staged_files, working_dir_files
            )
            status_dict[status].append(file_path)

        # Return the status dictionary
        return status_dict

    except Exception as e:
        # Log the error
        logger.error(f"Error getting repository status: {str(e)}")
        return {}


# Format the status output in a human-readable format
def format_status_output(status_dict: Dict[FileStatus, List[str]]) -> str:
    """
    Format the status output in a human-readable format.

    Args:
        status_dict (Dict[FileStatus, List[str]]): Dictionary mapping file statuses to
        lists of file paths.

    Returns:
        str: Formatted status output.
    """

    # Initialize the output list
    output = []

    # Changes to be committed
    staged_files = []
    staged_files.extend(
        (f"new file:   {f}" for f in status_dict[FileStatus.STAGED_NEW])
    )
    staged_files.extend(
        (f"modified:   {f}" for f in status_dict[FileStatus.STAGED_MODIFIED])
    )
    staged_files.extend(
        (f"deleted:    {f}" for f in status_dict[FileStatus.STAGED_DELETED])
    )

    # Changes to be committed
    if staged_files:
        if COLOR_SUPPORT:
            output.append(f"{Fore.GREEN}Changes to be committed:{Style.RESET_ALL}")
            unstage_msg = (
                f'  (use "{Fore.BLUE}clony reset HEAD <file>...{Style.RESET_ALL}" '
            )
            unstage_msg += "to unstage)"
            output.append(unstage_msg)
        else:
            output.append("Changes to be committed:")
            output.append('  (use "clony reset HEAD <file>..." to unstage)')
        output.append("")
        if COLOR_SUPPORT:
            output.extend(
                f"        {Fore.GREEN}{f}{Style.RESET_ALL}" for f in staged_files
            )
        else:
            output.extend(f"        {f}" for f in staged_files)
        output.append("")

    # Changes not staged for commit
    unstaged_files = []
    unstaged_files.extend(
        (f"modified:   {f}" for f in status_dict[FileStatus.MODIFIED])
    )
    unstaged_files.extend((f"deleted:    {f}" for f in status_dict[FileStatus.DELETED]))
    unstaged_files.extend(
        (f"modified:   {f}" for f in status_dict[FileStatus.BOTH_MODIFIED])
    )
    unstaged_files.extend(
        (f"deleted:    {f}" for f in status_dict[FileStatus.BOTH_DELETED])
    )

    # Changes not staged for commit
    if unstaged_files:
        if COLOR_SUPPORT:
            output.append(
                f"{Fore.YELLOW}Changes not staged for commit:{Style.RESET_ALL}"
            )
            update_msg = f'  (use "{Fore.BLUE}clony stage <file>...{Style.RESET_ALL}" '
            update_msg += "to update what will be committed)"
            output.append(update_msg)
        else:
            output.append("Changes not staged for commit:")
            output.append(
                '  (use "clony stage <file>..." to update what will be committed)'
            )
        output.append("")
        if COLOR_SUPPORT:
            output.extend(
                f"        {Fore.YELLOW}{f}{Style.RESET_ALL}" for f in unstaged_files
            )
        else:
            output.extend(f"        {f}" for f in unstaged_files)
        output.append("")

    # Untracked files
    untracked_files = status_dict[FileStatus.UNTRACKED]
    if untracked_files:
        if COLOR_SUPPORT:
            output.append(f"{Fore.RED}Untracked files:{Style.RESET_ALL}")
            include_msg = f'  (use "{Fore.BLUE}clony stage <file>...{Style.RESET_ALL}" '
            include_msg += "to include in what will be committed)"
            output.append(include_msg)
        else:
            output.append("Untracked files:")
            output.append(
                '  (use "clony stage <file>..." to include in what will be committed)'
            )
        output.append("")
        if COLOR_SUPPORT:
            output.extend(
                f"        {Fore.RED}{f}{Style.RESET_ALL}" for f in untracked_files
            )
        else:
            output.extend(f"        {f}" for f in untracked_files)
        output.append("")

    # Summary line
    if not any(status_dict.values()):
        msg = "nothing to commit, working tree clean"
        output.append(f"{Fore.GREEN}{msg}{Style.RESET_ALL}" if COLOR_SUPPORT else msg)

    # Return the formatted output
    return "\n".join(output)


# Get the status of the repository
def get_status(path: str = ".") -> Tuple[Dict[FileStatus, List[str]], str]:
    """
    Get the status of the repository and format it for display.

    Args:
        path (str, optional): Path to the repository. Defaults to ".".

    Returns:
        Tuple[Dict[FileStatus, List[str]], str]: A tuple containing:
            - Dict[FileStatus, List[str]]: Dictionary mapping file statuses to
              lists of file paths.
            - str: Formatted status output.
    """

    # Get the status of the repository
    status_dict = get_repository_status(path)

    # Format the status output
    formatted_output = format_status_output(status_dict)

    # Return the status dictionary and formatted output
    return status_dict, formatted_output


# Function to display repository status in tabular format
def display_status_info(status_dict: Dict[FileStatus, List[str]]) -> None:
    """
    Display repository status information in a formatted table.

    This function creates and displays formatted tables showing the status
    of files in the repository, including files staged for commit, files
    with changes not staged for commit, and untracked files.

    Args:
        status_dict (Dict[FileStatus, List[str]]): Dictionary mapping file statuses to
            lists of file paths.
    """

    try:
        # Check if there's anything to display
        if not any(status_dict.values()):
            # Create a table for empty status
            table = Table(title="Repository Status")

            # Add a column to the table
            table.add_column("Status", style="green")

            # Add a row indicating clean working tree
            table.add_row("Nothing to commit, working tree clean")

            # Display the table
            console.print(table)
            return

        # Create a table for staged files
        staged_files = (
            status_dict[FileStatus.STAGED_NEW]
            + status_dict[FileStatus.STAGED_MODIFIED]
            + status_dict[FileStatus.STAGED_DELETED]
        )

        if staged_files:
            # Create a table for changes to be committed
            staged_table = Table(title="Changes to be committed")

            # Add columns to the table
            staged_table.add_column("File", style="cyan")
            staged_table.add_column("Status", style="green")

            # Add information about how to unstage files
            logger.info("Use 'clony reset HEAD <file>...' to unstage")

            # Add rows for each staged file
            for file_path in status_dict[FileStatus.STAGED_NEW]:
                # Add row for new files
                staged_table.add_row(file_path, "New file")

            for file_path in status_dict[FileStatus.STAGED_MODIFIED]:
                # Add row for modified files
                staged_table.add_row(file_path, "Modified")

            for file_path in status_dict[FileStatus.STAGED_DELETED]:
                # Add row for deleted files
                staged_table.add_row(file_path, "Deleted")

            # Display the staged files table
            console.print(staged_table)

        # Create a table for unstaged changes
        unstaged_files = (
            status_dict[FileStatus.MODIFIED]
            + status_dict[FileStatus.DELETED]
            + status_dict[FileStatus.BOTH_MODIFIED]
            + status_dict[FileStatus.BOTH_DELETED]
        )

        if unstaged_files:
            # Create a table for changes not staged for commit
            unstaged_table = Table(title="Changes not staged for commit")

            # Add columns to the table
            unstaged_table.add_column("File", style="cyan")
            unstaged_table.add_column("Status", style="yellow")

            # Add information about how to stage changes
            logger.info("Use 'clony stage <file>...' to stage changes")

            # Add rows for each unstaged file
            for file_path in status_dict[FileStatus.MODIFIED]:
                # Add row for modified files
                unstaged_table.add_row(file_path, "Modified")

            for file_path in status_dict[FileStatus.DELETED]:
                # Add row for deleted files
                unstaged_table.add_row(file_path, "Deleted")

            for file_path in status_dict[FileStatus.BOTH_MODIFIED]:
                # Add row for files both staged and then modified again
                unstaged_table.add_row(file_path, "Modified")

            for file_path in status_dict[FileStatus.BOTH_DELETED]:
                # Add row for files both staged and then deleted
                unstaged_table.add_row(file_path, "Deleted")

            # Display the unstaged files table
            console.print(unstaged_table)

        # Create a table for untracked files
        untracked_files = status_dict[FileStatus.UNTRACKED]

        if untracked_files:
            # Create a table for untracked files
            untracked_table = Table(title="Untracked files")

            # Add a column to the table
            untracked_table.add_column("File", style="red")

            # Add information about how to track files
            logger.info(
                "Use 'clony stage <file>...' to include in what will be committed"
            )

            # Add rows for each untracked file
            for file_path in untracked_files:
                # Add row for untracked files
                untracked_table.add_row(file_path)

            # Display the untracked files table
            console.print(untracked_table)
    except Exception as e:
        # Log the error
        logger.error(f"Error displaying status: {str(e)}")
