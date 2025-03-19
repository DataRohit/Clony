"""
Log module for Clony.

This module handles the log functionality for the Clony Git clone tool,
allowing users to view the commit history.
"""

# Standard library imports
import zlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Third-party imports
from rich.console import Console
from rich.table import Table

# Local imports
from clony.core.refs import get_head_commit
from clony.internals.staging import find_git_repo_path
from clony.utils.logger import logger

# Initialize rich console for pretty output
console = Console()


# Function to read a Git object
def read_git_object(repo_path: Path, object_hash: str) -> Tuple[str, bytes]:
    """
    Read a Git object from the .git/objects directory.

    Args:
        repo_path (Path): Path to the repository.
        object_hash (str): The SHA-1 hash of the object.

    Returns:
        Tuple[str, bytes]: A tuple containing the object type and content.
    """

    # Define the object file path
    object_dir = repo_path / ".git" / "objects"
    object_file_path = object_dir / object_hash[:2] / object_hash[2:]

    # Check if the object file exists
    if not object_file_path.exists():
        logger.error(f"Object file not found: {object_hash}")
        return "", b""

    # Read and decompress the object file
    with open(object_file_path, "rb") as f:
        compressed_content = f.read()
    decompressed_content = zlib.decompress(compressed_content)

    # Parse the object header to get the type
    null_index = decompressed_content.find(b"\0")
    header = decompressed_content[:null_index].decode()
    content = decompressed_content[null_index + 1 :]

    # Extract the object type from the header
    object_type = header.split()[0]

    # Return the object type and content
    return object_type, content


# Function to parse a commit object
def parse_commit_object(content: bytes) -> Dict[str, str]:
    """
    Parse a commit object content.

    Args:
        content (bytes): The content of the commit object.

    Returns:
        Dict[str, str]: A dictionary containing the commit information.
    """

    # Initialize the commit info dictionary
    commit_info = {
        "tree": "",
        "parent": None,
        "author": "",
        "committer": "",
        "message": "",
    }

    # Convert bytes to string
    content_str = content.decode()

    # Split the content into header and message
    parts = content_str.split("\n\n", 1)
    header = parts[0]
    message = parts[1] if len(parts) > 1 else ""

    # Parse the header lines
    for line in header.split("\n"):
        if line.startswith("tree "):
            commit_info["tree"] = line[5:]
        elif line.startswith("parent "):
            commit_info["parent"] = line[7:]
        elif line.startswith("author "):
            commit_info["author"] = line[7:]
        elif line.startswith("committer "):
            commit_info["committer"] = line[10:]

    # Set the commit message
    commit_info["message"] = message.strip()

    # Return the commit info
    return commit_info


# Function to format the author/committer timestamp
def format_timestamp(timestamp_str: str) -> str:
    """
    Format the author/committer timestamp.

    Args:
        timestamp_str (str): The timestamp string from the commit object.

    Returns:
        str: A formatted timestamp string.
    """

    # Extract the timestamp and timezone
    parts = timestamp_str.split()
    timestamp = int(parts[-2])
    timezone = parts[-1]

    # Convert the timestamp to a datetime object
    dt = datetime.fromtimestamp(timestamp)

    # Format the datetime
    formatted_date = dt.strftime("%a %b %d %H:%M:%S %Y")

    # Return the formatted date with timezone
    return f"{formatted_date} {timezone}"


# Function to get the commit history
def get_commit_logs(repo_path: Optional[Path] = None) -> List[Dict[str, str]]:
    """
    Get the commit history starting from HEAD.

    Args:
        repo_path (Optional[Path]): Path to the repository. If None, the current
            directory is used.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing commit information.
    """

    # Find the repository path if not provided
    if repo_path is None:
        repo_path = find_git_repo_path(Path.cwd())
        if not repo_path:
            logger.error("Not a git repository. Run 'clony init' to create one.")
            return []

    # Get the HEAD commit
    current_commit = get_head_commit(repo_path)
    if not current_commit:
        return []

    # Initialize the commit history list
    commit_history = []

    # Traverse the commit history
    while current_commit:
        # Read the commit object
        object_type, content = read_git_object(repo_path, current_commit)

        # Check if the object is a commit
        if object_type != "commit":
            logger.error(f"Object {current_commit} is not a commit.")
            break

        # Parse the commit object
        commit_info = parse_commit_object(content)

        # Add the commit hash to the info
        commit_info["hash"] = current_commit

        # Add the commit to the history
        commit_history.append(commit_info)

        # Move to the parent commit
        current_commit = commit_info.get("parent")

    # Return the commit history
    return commit_history


# Function to display the commit history
def display_commit_logs(repo_path: Optional[Path] = None) -> None:
    """
    Display the commit history starting from HEAD.

    Args:
        repo_path (Optional[Path]): Path to the repository. If None, the current
            directory is used.
    """
    # If the repository path is not provided, find it
    if repo_path is None:
        repo_path = find_git_repo_path(Path.cwd())
        if not repo_path:
            logger.error("Not a git repository")
            return

    # Get the commit history
    commit_history = get_commit_logs(repo_path)

    # Check if there are any commits
    if not commit_history:
        logger.info("No commits found")
        return

    # Create a table for displaying commit information
    table = Table(title="Commit History")
    table.add_column("Commit Hash", style="cyan")
    table.add_column("Author", style="green")
    table.add_column("Date", style="yellow")
    table.add_column("Message", style="white")

    # Add each commit to the table
    for commit in commit_history:
        # Extract the author information
        author_info = commit.get("author", "")
        author_name = (
            author_info.split("<")[0].strip() if "<" in author_info else author_info
        )
        email = ""
        if "<" in author_info:
            email = author_info.split("<")[1].split(">")[0]

        # Format the timestamp
        formatted_date = format_timestamp(author_info)

        # Add the commit information to the table
        table.add_row(
            commit["hash"],
            f"{author_name} <{email}>" if email else author_name,
            formatted_date,
            commit["message"],
        )

    # Display the table
    console.print(table)
