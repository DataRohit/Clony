"""
Merge module for Clony.

This module provides the functionality for three-way merge algorithm
with conflict detection to integrate changes from different branches or commits.
"""

# Standard library imports
from pathlib import Path
from typing import Dict, List, Tuple, Union

# Third-party imports
from rich.console import Console
from rich.table import Table

# Local imports
from clony.core.diff import myers_diff, read_git_object
from clony.core.objects import parse_tree_object
from clony.core.repository import Repository
from clony.internals.log import parse_commit_object
from clony.utils.logger import logger

# Initialize console for Rich
console = Console()


# Function to identify changes between base content and modified content
def identify_changes(base_content: List[str], content: List[str]) -> Dict[int, str]:
    """
    Identify changes between base content and modified content.

    Args:
        base_content (List[str]): The base content.
        content (List[str]): The modified content.

    Returns:
        Dict[int, str]: A dictionary mapping line numbers to changed content.
    """

    # Use the Myers diff algorithm to identify changes
    diff_result = myers_diff(base_content, content)

    # Initialize a dictionary to store the changes
    changes = {}

    # Track the current line number in the modified content
    current_line = 0

    # Process the diff result
    for operation, line in diff_result:
        if operation == "+":
            # This is an addition
            changes[current_line] = line
            current_line += 1
        elif operation == " ":
            # This is an unchanged line
            current_line += 1

    # Return the changes
    return changes


# Function to detect conflicts between this and other changes compared to the base
def detect_conflicts(
    base_content: List[str], this_content: List[str], other_content: List[str]
) -> Tuple[List[str], List[Tuple[int, str, str]]]:
    """
    Detect conflicts between this and other changes compared to the base.

    Args:
        base_content (List[str]): The base content.
        this_content (List[str]): The content of the current branch.
        other_content (List[str]): The content of the branch to be merged.

    Returns:
        Tuple[List[str], List[Tuple[int, str, str]]]: A tuple containing
            the merged content and a list of conflicts
            (line number, this line, other line).
    """

    # Identify changes in both branches
    this_changes = identify_changes(base_content, this_content)
    other_changes = identify_changes(base_content, other_content)

    # Initialize the merged content with the base content
    merged_content = base_content.copy()

    # Initialize a list to store conflicts
    conflicts = []

    # Apply non-conflicting changes
    # First, collect all line numbers where changes occurred
    all_changed_lines = set(this_changes.keys()) | set(other_changes.keys())

    # For each changed line
    for line_num in sorted(all_changed_lines):
        # Check if the line was changed in both branches
        this_changed = line_num in this_changes
        other_changed = line_num in other_changes

        if this_changed and other_changed:
            # Conflict: both branches changed the same line
            this_line = this_changes[line_num]
            other_line = other_changes[line_num]

            if this_line != other_line:
                # Different changes to the same line - this is a conflict
                conflicts.append((line_num, this_line, other_line))
                # Keep this branch's version in the merged content for now
                if line_num < len(merged_content):
                    merged_content[line_num] = this_line
                else:
                    merged_content.append(this_line)
            else:
                # Both branches made the same change - no conflict
                if line_num < len(merged_content):
                    merged_content[line_num] = this_line
                else:
                    merged_content.append(this_line)
        elif this_changed:
            # Only this branch changed the line
            if line_num < len(merged_content):
                merged_content[line_num] = this_changes[line_num]
            else:
                merged_content.append(this_changes[line_num])
        elif other_changed:
            # Only other branch changed the line
            if line_num < len(merged_content):
                merged_content[line_num] = other_changes[line_num]
            else:
                merged_content.append(other_changes[line_num])

    # Return the merged content and conflicts
    return merged_content, conflicts


# Function to perform a three-way merge between base, this, and other commits
def three_way_merge(
    repo_path: Path, base_hash: str, this_hash: str, other_hash: str
) -> Dict[str, Dict[str, Union[List[str], List[Tuple[int, str, str]]]]]:
    """
    Perform a three-way merge between base, this, and other commits.

    Args:
        repo_path (Path): Path to the repository.
        base_hash (str): The hash of the base commit.
        this_hash (str): The hash of the current commit.
        other_hash (str): The hash of the commit to be merged.

    Returns:
        Dict[str, Dict[str, Union[List[str], List[Tuple[int, str, str]]]]]: A dictionary
            mapping file paths to dictionaries containing merged content and conflicts.
    """

    # Parse the commit objects to get the tree hashes
    _, base_tree_hash = parse_commit_object(repo_path, base_hash)
    _, this_tree_hash = parse_commit_object(repo_path, this_hash)
    _, other_tree_hash = parse_commit_object(repo_path, other_hash)

    # Get the list of files in each tree
    base_files = get_files_in_tree(repo_path, base_tree_hash)
    this_files = get_files_in_tree(repo_path, this_tree_hash)
    other_files = get_files_in_tree(repo_path, other_tree_hash)

    # Combine all file paths
    all_files = (
        set(base_files.keys()) | set(this_files.keys()) | set(other_files.keys())
    )

    # Initialize the result dictionary
    result = {}

    # Process each file
    for file_path in all_files:
        # Get the blob hashes for each file
        base_blob = base_files.get(file_path)
        this_blob = this_files.get(file_path)
        other_blob = other_files.get(file_path)

        # If the file exists in all three commits, perform a three-way merge
        if base_blob and this_blob and other_blob:
            # Read the file contents
            base_type, base_content = read_git_object(repo_path, base_blob)
            this_type, this_content = read_git_object(repo_path, this_blob)
            other_type, other_content = read_git_object(repo_path, other_blob)

            # Skip binary files
            if (
                is_binary_content(base_content)
                or is_binary_content(this_content)
                or is_binary_content(other_content)
            ):
                logger.warning(f"Skipping binary file: {file_path}")
                result[file_path] = {
                    "merged_content": [],
                    "conflicts": [(-1, "Binary file", "Binary file")],
                    "is_binary": True,
                }
                continue

            # Convert the content to text
            base_text = base_content.decode("utf-8")
            this_text = this_content.decode("utf-8")
            other_text = other_content.decode("utf-8")

            # Split the text into lines
            base_lines = base_text.splitlines()
            this_lines = this_text.splitlines()
            other_lines = other_text.splitlines()

            # Perform the three-way merge
            merged_content, conflicts = detect_conflicts(
                base_lines, this_lines, other_lines
            )

            # Store the result
            result[file_path] = {
                "merged_content": merged_content,
                "conflicts": conflicts,
                "is_binary": False,
            }
        elif not base_blob:
            # File was added in at least one of the branches
            if this_blob and other_blob:
                # File was added in both branches, check for conflicts
                _, this_content = read_git_object(repo_path, this_blob)
                _, other_content = read_git_object(repo_path, other_blob)

                # Skip binary files
                if is_binary_content(this_content) or is_binary_content(other_content):
                    logger.warning(f"Skipping binary file: {file_path}")
                    result[file_path] = {
                        "merged_content": [],
                        "conflicts": [(-1, "Binary file", "Binary file")],
                        "is_binary": True,
                    }
                    continue

                # Convert the content to text
                this_text = this_content.decode("utf-8")
                other_text = other_content.decode("utf-8")

                # Split the text into lines
                this_lines = this_text.splitlines()
                other_lines = other_text.splitlines()

                # Check if the files are identical
                if this_lines == other_lines:
                    # No conflict, use either version
                    result[file_path] = {
                        "merged_content": this_lines,
                        "conflicts": [],
                        "is_binary": False,
                    }
                else:
                    # Conflict: file was added differently in both branches
                    result[file_path] = {
                        "merged_content": this_lines,
                        "conflicts": [
                            (
                                0,
                                "File added in this branch",
                                "File added in other branch",
                            )
                        ],
                        "is_binary": False,
                    }
            elif this_blob:
                # File was added only in this branch, use it
                _, this_content = read_git_object(repo_path, this_blob)

                # Skip binary files
                if is_binary_content(this_content):
                    logger.warning(f"Skipping binary file: {file_path}")
                    result[file_path] = {
                        "merged_content": [],
                        "conflicts": [],
                        "is_binary": True,
                    }
                    continue

                # Convert the content to text
                this_text = this_content.decode("utf-8")

                # Split the text into lines
                this_lines = this_text.splitlines()

                # Store the result
                result[file_path] = {
                    "merged_content": this_lines,
                    "conflicts": [],
                    "is_binary": False,
                }
            else:
                # File was added only in other branch, use it
                _, other_content = read_git_object(repo_path, other_blob)

                # Skip binary files
                if is_binary_content(other_content):
                    logger.warning(f"Skipping binary file: {file_path}")
                    result[file_path] = {
                        "merged_content": [],
                        "conflicts": [],
                        "is_binary": True,
                    }
                    continue

                # Convert the content to text
                other_text = other_content.decode("utf-8")

                # Split the text into lines
                other_lines = other_text.splitlines()

                # Store the result
                result[file_path] = {
                    "merged_content": other_lines,
                    "conflicts": [],
                    "is_binary": False,
                }
        elif not this_blob:
            # File was deleted in this branch
            if other_blob:
                # File was deleted in this branch but modified in other branch
                # This is a conflict
                result[file_path] = {
                    "merged_content": [],
                    "conflicts": [
                        (
                            0,
                            "File deleted in this branch",
                            "File modified in other branch",
                        )
                    ],
                    "is_binary": False,
                }
            else:
                # File was deleted in both branches - no conflict
                result[file_path] = {
                    "merged_content": [],
                    "conflicts": [],
                    "is_binary": False,
                }
        elif not other_blob:
            # File was deleted in other branch but exists in this branch - conflict
            result[file_path] = {
                "merged_content": [],
                "conflicts": [
                    (0, "File modified in this branch", "File deleted in other branch")
                ],
                "is_binary": False,
            }

    # Return the result
    return result


# Function to get all files in a tree object
def get_files_in_tree(repo_path: Path, tree_hash: str) -> Dict[str, str]:
    """
    Get all files in a tree object.

    Args:
        repo_path (Path): Path to the repository.
        tree_hash (str): The hash of the tree object.

    Returns:
        Dict[str, str]: A dictionary mapping file paths to blob hashes.
    """

    # Initialize the result dictionary
    files = {}

    # Read the tree object
    obj_type, content = read_git_object(repo_path, tree_hash)

    # Ensure it's a tree object
    if obj_type != "tree":
        logger.error(f"Object {tree_hash} is not a tree")
        return {}

    # Parse the tree object
    tree_entries = parse_tree_object(content)

    # Process each entry in the tree
    for mode, obj_type, obj_hash, name in tree_entries:
        if obj_type == "blob":
            # This is a file
            files[name] = obj_hash
        elif obj_type == "tree":
            # This is a directory, recursively process it
            subtree_files = get_files_in_tree(repo_path, obj_hash)
            for subpath, subhash in subtree_files.items():
                files[f"{name}/{subpath}"] = subhash

    # Return the files
    return files


# Function to check if the content is binary
def is_binary_content(content: bytes) -> bool:
    """
    Check if the content is binary.

    Args:
        content (bytes): The content to check.

    Returns:
        bool: True if the content is binary, False otherwise.
    """

    # NUL byte usually indicates binary content
    if b"\0" in content:
        return True

    # Try to decode as UTF-8
    try:
        content.decode("utf-8")
        return False
    except UnicodeDecodeError:
        return True


# Function to display the results of a three-way merge
def display_merge_results(
    merge_results: Dict[str, Dict[str, Union[List[str], List[Tuple[int, str, str]]]]],
) -> int:
    """
    Display the results of a three-way merge.

    Args:
        merge_results: The merge results mapping file paths to merge info.

    Returns:
        int: The number of conflicts found.
    """

    # Count the total number of conflicts
    total_conflicts = 0

    # Create a table for the merge results
    table = Table(title="Merge Results", border_style="blue")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Conflicts", style="red")

    # Process each file
    for file_path, result in merge_results.items():
        conflicts = result["conflicts"]
        num_conflicts = len(conflicts)
        total_conflicts += num_conflicts

        if num_conflicts > 0:
            status = "Conflicts"
            conflicts_text = str(num_conflicts)
        else:
            status = "Merged"
            conflicts_text = "0"

        # Add the row to the table
        table.add_row(file_path, status, conflicts_text)

    # Print the table
    console.print(table)

    # Display conflict details if there are conflicts
    if total_conflicts > 0:
        console.print()
        logger.error("Conflicts were found during the merge:")

        for file_path, result in merge_results.items():
            conflicts = result["conflicts"]

            if conflicts:
                console.print()
                logger.error(f"File: {file_path}")

                # Create a table for the conflicts
                conflict_table = Table(border_style="red")
                conflict_table.add_column("Line", style="blue")
                conflict_table.add_column("This Branch", style="green")
                conflict_table.add_column("Other Branch", style="yellow")

                # Add each conflict to the table
                for line_num, this_line, other_line in conflicts:
                    conflict_table.add_row(str(line_num), this_line, other_line)

                # Print the conflict table
                console.print(conflict_table)

    # Return the total number of conflicts
    return total_conflicts


# Function to perform a three-way merge with the current branch
def perform_merge(base_hash: str, other_hash: str) -> int:
    """
    Perform a three-way merge with the current branch.

    Args:
        base_hash (str): The hash of the base commit.
        other_hash (str): The hash of the commit to be merged.

    Returns:
        int: The number of conflicts found.
    """

    # Get the repository path
    repo_path = Path.cwd()

    # Get the current repository
    repo = Repository(repo_path)

    # Get the current branch
    this_hash = repo.get_head_commit()

    # Perform the three-way merge
    merge_results = three_way_merge(repo_path, base_hash, this_hash, other_hash)

    # Display the merge results
    num_conflicts = display_merge_results(merge_results)

    # Return the number of conflicts
    return num_conflicts
