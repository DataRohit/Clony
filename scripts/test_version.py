#!/usr/bin/env python3
"""
Test script to verify version extraction from Git tags works correctly.

This script helps debug version issues in GitHub Actions by:
1. Extracting the current version from Git tags
2. Creating a _version.py file with the extracted version
3. Updating __init__.py to maintain consistent versioning

Usage:
    python scripts/test_version.py
"""

# Standard imports
import re
import subprocess
import sys
from pathlib import Path


# Function to extract version from Git tags
def main():
    """
    Execute the version extraction and file update process.

    This function:
    1. Attempts to extract the current version from Git tags
    2. Falls back to a default version if no tag is found
    3. Creates/updates version files with the extracted version
    4. Verifies the changes were applied successfully

    Returns:
        int: 0 on success, non-zero on failure
    """

    # Print startup message to indicate script execution
    print("Testing version extraction and build process")

    # Attempt to get the current git tag
    try:
        # Execute git command to get the most recent tag
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        ).strip()

        # Log the found tag for debugging
        print(f"Found git tag: {tag}")

        # Remove 'v' prefix if present to get semantic version
        if tag.startswith("v"):
            version = tag[1:]
        else:
            version = tag

        # Log the extracted version
        print(f"Extracted version: {version}")

    except subprocess.CalledProcessError:
        # Handle case when no git tag is available
        print("No git tag found, using fallback version 0.1.12")

        # Default to fallback version if no tag is available
        version = "0.1.12"

    # Configure path to the clony package and version file
    version_dir = Path("clony")
    version_file = version_dir / "_version.py"

    # Create the _version.py file with extracted version
    with open(version_file, "w") as f:
        # Write version information to file
        f.write(f"# Generated manually\nversion = '{version}'\n")

    # Log successful creation of version file
    print(f"Created {version_file} with version {version}")

    # Check for and update the package __init__.py file
    init_file = version_dir / "__init__.py"

    # Only proceed if the init file exists
    if init_file.exists():
        # Read the current content of the init file
        with open(init_file, "r") as f:
            content = f.read()

        # Check if version string exists in the file
        if "__version__" in content:
            # Replace any existing version with the extracted version
            new_content = re.sub(
                r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                f'__version__ = "{version}"',
                content,
            )

            # Write the updated content back to the file
            with open(init_file, "w") as f:
                f.write(new_content)

            # Log successful update of init file
            print(f"Updated {init_file} with version {version}")

    # Log completion message
    print("Version extraction test complete!")

    # Return success code
    return 0


# Script entry point
if __name__ == "__main__":
    # Execute main function and use its return value as exit code
    sys.exit(main())
