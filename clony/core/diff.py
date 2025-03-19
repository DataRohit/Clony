"""
Diff functionality for Clony.

This module provides the functionality to compare blob objects and
display line-by-line differences.
"""

# Standard library imports
import difflib
import zlib
from pathlib import Path
from typing import List, Optional, Tuple

# Third-party imports
try:
    import colorama
    from colorama import Fore, Style

    colorama.init()
    COLOR_SUPPORT = True
except ImportError:
    COLOR_SUPPORT = False

# Local imports
from clony.utils.logger import logger


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


# Function to implement the Myers diff algorithm
def myers_diff(a: List[str], b: List[str]) -> List[Tuple[str, str]]:
    """
    Implement the Myers diff algorithm to compare two lists of strings.

    Args:
        a (List[str]): The first list of strings.
        b (List[str]): The second list of strings.

    Returns:
        List[Tuple[str, str]]: A list of tuples, where each tuple contains
            the operation and the line content.
    """

    # Initialize the sequence matcher
    matcher = difflib.SequenceMatcher(None, a, b)

    # Get the opcodes (operations) for the differences
    opcodes = matcher.get_opcodes()

    # Initialize the result list
    result = []

    # Process each opcode
    for tag, i1, i2, j1, j2 in opcodes:
        # Process each opcode based on the tag
        if tag == "equal":
            # Equal lines
            for i in range(i1, i2):
                result.append((" ", a[i]))
        elif tag == "replace":
            # Replace lines
            for i in range(i1, i2):
                result.append(("-", a[i]))
            for j in range(j1, j2):
                result.append(("+", b[j]))
        elif tag == "delete":
            # Delete lines
            for i in range(i1, i2):
                result.append(("-", a[i]))
        elif tag == "insert":
            # Insert lines
            for j in range(j1, j2):
                result.append(("+", b[j]))

    # Return the result
    return result


# Function to colorize the diff output
def colorize_diff_line(line: Tuple[str, str]) -> str:
    """
    Colorize a diff line based on the operation.

    Args:
        line (Tuple[str, str]): A tuple containing the operation and the line content.

    Returns:
        str: The colorized line.
    """

    # Extract the operation and content
    op, content = line

    # Check if color support is available
    if COLOR_SUPPORT:
        # Colorize based on operation
        if op == "+":
            return f"{Fore.GREEN}{op} {content}{Style.RESET_ALL}"
        elif op == "-":
            return f"{Fore.RED}{op} {content}{Style.RESET_ALL}"
        else:
            return f"{op} {content}"
    else:
        # Return uncolored output if no color support
        return f"{op} {content}"


# Function to colorize unified diff lines
def colorize_unified_diff_line(line: str) -> str:
    """
    Colorize a unified diff line based on its prefix.

    Args:
        line (str): A unified diff line.

    Returns:
        str: The colorized line.
    """

    # Check if color support is available
    if not COLOR_SUPPORT or not line:
        return line

    # Colorize the line based on its prefix
    if line.startswith("+++"):
        # File header (added file)
        return f"{Fore.BLUE}{line}{Style.RESET_ALL}"
    elif line.startswith("---"):
        # File header (removed file)
        return f"{Fore.BLUE}{line}{Style.RESET_ALL}"
    elif line.startswith("+"):
        # Added line
        return f"{Fore.GREEN}{line}{Style.RESET_ALL}"
    elif line.startswith("-"):
        # Removed line
        return f"{Fore.RED}{line}{Style.RESET_ALL}"
    elif line.startswith("@@"):
        # Hunk header
        return f"{Fore.CYAN}{line}{Style.RESET_ALL}"
    else:
        # Context line or other
        return line


# Function to generate a unified diff
def generate_unified_diff(
    a_lines: List[str],
    b_lines: List[str],
    a_path: str = "a",
    b_path: str = "b",
    context_lines: int = 3,
) -> List[str]:
    """
    Generate a unified diff for two lists of strings.

    Args:
        a_lines (List[str]): The first list of strings.
        b_lines (List[str]): The second list of strings.
        a_path (str, optional): The path of the first file. Defaults to "a".
        b_path (str, optional): The path of the second file. Defaults to "b".
        context_lines (int, optional): The number of context lines. Defaults to 3.

    Returns:
        List[str]: The unified diff.
    """

    # Generate the unified diff
    diff = difflib.unified_diff(
        a_lines, b_lines, a_path, b_path, n=context_lines, lineterm=""
    )

    # Convert the diff to a list
    return list(diff)


# Function to is_binary_content to check if content is binary
def is_binary_content(content: bytes) -> bool:
    """
    Check if the content is binary.

    Args:
        content (bytes): The content to check.

    Returns:
        bool: True if the content is binary, False otherwise.
    """

    # Check if the content contains null bytes (indicating binary content)
    if b"\x00" in content:
        return True

    # Try to decode the content as UTF-8
    try:
        content.decode("utf-8")
        return False
    except UnicodeDecodeError:
        return True


# Function to compute differences between two blobs
def diff_blobs(
    repo_path: Path,
    blob1_hash: str,
    blob2_hash: str,
    path1: Optional[str] = None,
    path2: Optional[str] = None,
    algorithm: str = "myers",
    context_lines: int = 3,
) -> List[str]:
    """
    Compute the differences between two blob objects.

    Args:
        repo_path (Path): Path to the repository.
        blob1_hash (str): The SHA-1 hash of the first blob.
        blob2_hash (str): The SHA-1 hash of the second blob.
        path1 (Optional[str], optional): The path of the first file. Defaults to None.
        path2 (Optional[str], optional): The path of the second file. Defaults to None.
        algorithm (str, optional): The diff algorithm to use. Defaults to "myers".
        context_lines (int, optional): The number of context lines. Defaults to 3.

    Returns:
        List[str]: The differences between the blobs.
    """

    # Read the blob objects
    blob1_type, blob1_content = read_git_object(repo_path, blob1_hash)
    blob2_type, blob2_content = read_git_object(repo_path, blob2_hash)

    # Check if the objects are blobs
    if blob1_type != "blob" or blob2_type != "blob":
        logger.error(f"Objects are not blobs: {blob1_hash}, {blob2_hash}")
        return []

    # Check if either content is binary
    if is_binary_content(blob1_content) or is_binary_content(blob2_content):
        logger.info("Binary files differ")
        return ["Binary files differ"]

    # Convert the content to text (safe to do now since we've checked for binary)
    blob1_text = blob1_content.decode("utf-8")
    blob2_text = blob2_content.decode("utf-8")

    # Split the text into lines
    blob1_lines = blob1_text.splitlines()
    blob2_lines = blob2_text.splitlines()

    # Set default paths if not provided
    path1 = path1 or f"a/{blob1_hash[:7]}"
    path2 = path2 or f"b/{blob2_hash[:7]}"

    # Generate the diff based on the algorithm
    if algorithm == "myers":
        # Use the Myers diff algorithm
        diff_lines = myers_diff(blob1_lines, blob2_lines)

        # Format the diff lines
        return [colorize_diff_line(line) for line in diff_lines]
    else:
        # Use the unified diff format
        unified_diff = generate_unified_diff(
            blob1_lines, blob2_lines, path1, path2, context_lines
        )

        # Colorize each line in the unified diff
        return [colorize_unified_diff_line(line) for line in unified_diff]


# Function to print the diff
def print_diff(
    repo_path: Path,
    blob1_hash: str,
    blob2_hash: str,
    path1: Optional[str] = None,
    path2: Optional[str] = None,
    algorithm: str = "myers",
    context_lines: int = 3,
) -> None:
    """
    Print the differences between two blob objects.

    Args:
        repo_path (Path): Path to the repository.
        blob1_hash (str): The SHA-1 hash of the first blob.
        blob2_hash (str): The SHA-1 hash of the second blob.
        path1 (Optional[str], optional): The path of the first file. Defaults to None.
        path2 (Optional[str], optional): The path of the second file. Defaults to None.
        algorithm (str, optional): The diff algorithm to use. Defaults to "myers".
        context_lines (int, optional): The number of context lines. Defaults to 3.
    """

    # Generate the diff
    diff_lines = diff_blobs(
        repo_path, blob1_hash, blob2_hash, path1, path2, algorithm, context_lines
    )

    # Print the diff
    for line in diff_lines:
        print(line)
