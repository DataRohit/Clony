"""
Commit module for Clony.

This module handles the commit functionality for the Clony Git clone tool.
"""

# Standard library imports
import sys
from pathlib import Path

# Local imports
from clony.core.objects import create_commit_object, create_tree_object
from clony.core.refs import get_head_commit, get_head_ref, update_ref
from clony.internals.staging import clear_staging_area, find_git_repo_path
from clony.utils.logger import logger


# Function to read the index file
def read_index_file(index_file: Path) -> dict:
    """
    Read the index file and return a dictionary of file paths and their SHA-1 hashes.

    Args:
        index_file (Path): Path to the .git/index file.

    Returns:
        dict: A dictionary mapping file paths to their SHA-1 hashes.
    """

    # Initialize an empty dictionary
    index_dict = {}

    # Check if the index file exists
    if not index_file.exists():
        return index_dict

    # Read the index file
    with open(index_file, "r") as f:
        lines = f.readlines()

    # Parse each line in the index file
    for line in lines:
        # Split the line into parts
        parts = line.strip().split()

        # If the line has two parts, add them to the dictionary
        if len(parts) == 2:
            file_path, sha1_hash = parts
            index_dict[file_path] = sha1_hash

    # Return the dictionary
    return index_dict


# Function to create a commit
def make_commit(message: str, author_name: str, author_email: str) -> str:
    """
    Create a commit with the staged changes.

    Args:
        message (str): The commit message.
        author_name (str): The name of the author.
        author_email (str): The email of the author.

    Returns:
        str: The SHA-1 hash of the commit.
    """

    try:
        # Find the repository path
        repo_path = find_git_repo_path(Path.cwd())
        if not repo_path:
            logger.error("Not a git repository. Run 'clony init' to create one.")
            sys.exit(1)

        # Define the index file path
        index_file = repo_path / ".git" / "index"

        # Check if the index file exists
        if not index_file.exists():
            logger.error(
                "Nothing to commit. Run 'clony stage <file>' to stage changes."
            )
            sys.exit(1)

        # Read the index file
        index_dict = read_index_file(index_file)

        # Check if there are any staged changes
        if not index_dict:
            logger.error(
                "Nothing to commit. Run 'clony stage <file>' to stage changes."
            )
            sys.exit(1)

        # Create a tree object for the root directory
        tree_hash = create_tree_object(repo_path, repo_path)

        # Get the current HEAD commit
        parent_hash = get_head_commit(repo_path)

        # Create a commit object
        commit_hash = create_commit_object(
            repo_path, tree_hash, parent_hash, author_name, author_email, message
        )

        # Update the current branch reference
        head_ref = get_head_ref(repo_path)
        if head_ref.startswith("refs/"):
            update_ref(repo_path, head_ref, commit_hash)
        else:
            # Update HEAD directly (detached HEAD state)
            with open(repo_path / ".git" / "HEAD", "w") as f:
                f.write(commit_hash + "\n")

        # Log the successful commit
        logger.info(f"Created commit {commit_hash[:7]} with message: {message}")

        # Clear the staging area after successful commit
        clear_staging_area(repo_path)
        logger.info("Staging area cleared")

        # Return the commit hash
        return commit_hash

    except Exception as e:
        # Log the error and exit
        logger.error(f"Error creating commit: {str(e)}")
        sys.exit(1)
