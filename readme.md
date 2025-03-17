# Clony

<div align="center">

<pre>
    ██████╗██╗      ██████╗ ███╗   ██╗██╗   ██╗
   ██╔════╝██║     ██╔═══██╗████╗  ██║╚██╗ ██╔╝
   ██║     ██║     ██║   ██║██╔██╗ ██║ ╚████╔╝ 
   ██║     ██║     ██║   ██║██║╚██╗██║  ╚██╔╝  
   ╚██████╗███████╗╚██████╔╝██║ ╚████║   ██║   
    ╚═════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   
</pre>

**🛠️ A modern Git clone tool with a colorful CLI interface. ✨ Clony provides intuitive Git commands with clear output, smart file staging, and flexible repository management.**

<p>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python Version"></a>
  <a href="license"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  <a href="https://pytest-cov.readthedocs.io/"><img src="https://img.shields.io/badge/coverage-100%25-brightgreen" alt="Test Coverage"></a>
</p>

</div>

## ✨ Features

- 🎨 **Modern CLI interface** with Rich for colorful, clear output
- 🔧 **Git repo management** with init and basic operations
- 📂 **Smart file staging** preventing unchanged file commits
- 🔄 **Flexible commit system** with custom messages and authors
- 🔙 **Multi-mode reset** supporting soft, mixed, and hard resets
- 🧩 **Modular architecture** for easy extensibility
- 📊 **100% test coverage** ensuring reliability
- 🚀 **Intuitive commands** with consistent syntax
- 🛡️ **Clear error handling** with actionable messages
- 📝 **Detailed logging** for debugging operations
- 🔍 **Transparent internals** for educational purposes

## 📋 Table of Contents

- [Installation](#-installation)
- [Usage](#-usage)
- [Development](#-development)
- [License](#-license)

## 🔧 Installation

### Prerequisites

- Python 3.10 or higher
- Git (for cloning the repository)

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/DataRohit/clony.git
cd clony

# Set up virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
source .venv/Scripts/activate
# On Linux/Mac:
# source .venv/bin/activate

# Install the package in development mode
pip install -e .

# Verify installation
clony --version
```

### Installing for Development

If you plan to contribute to Clony, install the development dependencies:

```bash
pip install -e ".[dev]"
```

### Troubleshooting

- **Command not found**: Ensure your virtual environment is activated and the package is installed
- **Import errors**: Make sure you've installed the package with `pip install -e .`
- **Permission issues**: On Linux/Mac, you might need to make the run_checks.sh script executable with `chmod +x run_checks.sh`

## 🚀 Usage

### Available Commands

#### Global Options

The following options are available for all commands:

```bash
--help, -h     # Show help information for any command
--version, -v  # Display version information
```

#### `help`

Display detailed help information about available commands and options.

```bash
# Show general help information with logo
clony help

# Show help for a specific command
clony init --help
```

#### `init`

Initialize a new Git repository in the specified directory.

```bash
# Basic Usage
clony init [path]  # Create a new Git repository

# Options
--force, -f       # Force reinitialization if repository exists
--help, -h        # Show help for init command
```

**Examples:**

```bash
# Initialize in current directory
$ clony init
INFO     Git repository initialized successfully
INFO     Initialized empty Git repository in /current/path

# Initialize in a new directory
$ clony init my-project
INFO     Git repository initialized successfully
INFO     Initialized empty Git repository in /path/to/my-project

# Try to initialize in existing repository
$ clony init existing-repo
WARNING  Git repository already exists
INFO     Use --force to reinitialize

# Force reinitialization
$ clony init existing-repo --force
INFO     Git repository initialized successfully
INFO     Initialized empty Git repository in /path/to/existing-repo

# Initialize with invalid path
$ clony init /invalid/path
ERROR    Parent directory does not exist: /invalid/path
```

#### `stage`

Stage a file by adding its content to the staging area. This command prepares a file to be included in the next commit by creating a blob object from the file content and updating the index.

The command will prevent staging files that haven't changed since the last commit, ensuring that only meaningful changes are committed. This check is performed regardless of whether the file is currently in the staging area or not, which means that even after a commit (which clears the staging area), you cannot stage a file that hasn't changed since that commit.

```bash
# Basic Usage
clony stage <file_path>  # Stage a file for the next commit

# Options
--help, -h              # Show help for stage command
```

**Examples:**

```bash
# Stage a file
$ clony stage myfile.txt
INFO     File staged: 'myfile.txt'

# Try to stage a non-existent file
$ clony stage non_existent_file.txt
ERROR    File not found: 'non_existent_file.txt'

# Stage a file in a non-git repository
$ clony stage file_outside_repo.txt
ERROR    Not a git repository. Run 'clony init' to create one.

# Try to stage a file that's already staged
$ clony stage already_staged.txt
WARNING  File already staged: 'already_staged.txt'

# Stage a file after changing its content
$ echo "Changed content" > myfile.txt
$ clony stage myfile.txt
INFO     File staged: 'myfile.txt'

# Try to stage a file with invalid path
$ clony stage /invalid/path/file.txt
ERROR    File not found: '/invalid/path/file.txt'

# Try to stage an unchanged file
$ clony stage unchanged_file.txt
WARNING  File unchanged since last commit: 'unchanged_file.txt'

# Try to stage an unchanged file after a commit (this will still fail)
$ clony commit --message "Initial commit"
INFO     Created commit a1b2c3d with message: Initial commit
INFO     Staging area cleared
$ clony stage unchanged_file.txt
WARNING  File unchanged since last commit: 'unchanged_file.txt'

# Stage a file after modifying it
$ echo "New content" > unchanged_file.txt
$ clony stage unchanged_file.txt
INFO     File staged: 'unchanged_file.txt'
```

#### `commit`

Create a new commit with the staged changes. This command creates a new commit object with the staged changes, including a tree object representing the directory structure and a reference to the parent commit.

The commit message is required, while author name and email are optional and will default to "Clony User" and "user@example.com" if not provided.

After a successful commit, the staging area is automatically cleared, ensuring a clean state for the next set of changes.

```bash
# Basic Usage
clony commit --message "Your commit message"  # Create a commit with staged changes

# Options
--message, -m         # The commit message (required)
--author-name         # The name of the author (defaults to "Clony User")
--author-email        # The email of the author (defaults to "user@example.com")
--help, -h            # Show help for commit command
```

**Examples:**

```bash
# Create a basic commit
$ clony commit --message "Initial commit"
INFO     Created commit a1b2c3d with message: Initial commit

# Create a commit with author information
$ clony commit --message "Add feature" --author-name "John Doe" --author-email "john@example.com"
INFO     Created commit e4f5g6h with message: Add feature

# Try to commit without a message
$ clony commit
ERROR    Missing option '--message' / '-m'.

# Try to commit with no staged changes
$ clony commit --message "Empty commit"
ERROR    Nothing to commit. Run 'clony stage <file>' to stage changes.

# Try to commit outside a git repository
$ clony commit --message "Outside repo"
ERROR    Not a git repository. Run 'clony init' to create one.
```

#### `reset`

Reset the current HEAD to a specified commit. This command updates the HEAD to point to the specified commit, and optionally updates the index and working directory to match.

The reset command supports three modes:
1. **Soft Reset (--soft)**: Move HEAD to the specified commit without changing the index or working directory.
2. **Mixed Reset (--mixed)**: Move HEAD to the specified commit and update the index to match, but leave the working directory unchanged. This is the default mode.
3. **Hard Reset (--hard)**: Move HEAD to the specified commit and update both the index and working directory to match.

```bash
# Basic Usage
clony reset <commit>  # Reset HEAD to the specified commit

# Options
--soft               # Move HEAD without changing the index or working directory
--mixed              # Move HEAD and update the index (default)
--hard               # Move HEAD and update both the index and working directory
--help, -h           # Show help for reset command
```

**Examples:**

```bash
# Perform a mixed reset (default)
$ clony reset abc123
INFO     Reset HEAD to abc123 (mixed mode)

# Perform a soft reset
$ clony reset --soft abc123
INFO     Reset HEAD to abc123 (soft mode)

# Perform a hard reset
$ clony reset --hard abc123
INFO     Reset HEAD to abc123 (hard mode)

# Reset to a branch name
$ clony reset main
INFO     Reset HEAD to def456 (mixed mode)

# Reset to a tag
$ clony reset v1.0
INFO     Reset HEAD to ghi789 (mixed mode)

# Try to reset with an invalid commit reference
$ clony reset invalid-commit
ERROR    Failed to reset HEAD to invalid-commit

# Try to reset outside a git repository
$ clony reset abc123
ERROR    Not in a Git repository
```

#### `status`

Show the working tree status. This command displays the state of the working directory and the staging area, showing which changes have been staged, which haven't, and which files aren't being tracked by Git.

The status command categorizes files into three main sections:
1. **Changes to be committed**: Files that have been staged and are ready for the next commit
2. **Changes not staged for commit**: Files that have been modified but not yet staged
3. **Untracked files**: Files that are not tracked by Git

```bash
# Basic Usage
clony status [path]  # Show the status of the working tree

# Options
--help, -h          # Show help for status command
```

**Examples:**

```bash
# Show status in current directory
$ clony status
On branch main

Untracked files:
  (use "clony stage <file>..." to include in what will be committed)

        file1.txt
        file2.txt

# Show status after staging a file
$ clony stage file1.txt
INFO     File staged: 'file1.txt'
$ clony status
On branch main

Changes to be committed:
  (use "clony reset HEAD <file>..." to unstage)

        new file:   file1.txt

Untracked files:
  (use "clony stage <file>..." to include in what will be committed)

        file2.txt

# Show status after committing
$ clony commit --message "Add file1.txt"
INFO     Created commit a1b2c3d with message: Add file1.txt
INFO     Staging area cleared
$ clony status
On branch main

Untracked files:
  (use "clony stage <file>..." to include in what will be committed)

        file2.txt

# Show status after modifying a committed file
$ echo "Modified content" > file1.txt
$ clony status
On branch main

Changes not staged for commit:
  (use "clony stage <file>..." to update what will be committed)

        modified:   file1.txt

Untracked files:
  (use "clony stage <file>..." to include in what will be committed)

        file2.txt

# Show status in a specific directory
$ clony status /path/to/repo
On branch main

nothing to commit, working tree clean

# Show status in a non-git repository
$ clony status /not/a/repo
ERROR    Not a git repository. Run 'clony init' to create one.
```

#### `log`

Display the commit history. This command traverses the commit graph starting from HEAD and displays the commit history in reverse chronological order (most recent first).

For each commit, the following information is displayed:
1. **Commit Hash**: The unique SHA-1 identifier of the commit
2. **Author**: The name and email of the individual who made the commit
3. **Date**: The exact date and time when the commit was made
4. **Commit Message**: The message describing the changes introduced in the commit

```bash
# Basic Usage
clony log  # Display the commit history

# Options
--help, -h  # Show help for log command
```

**Examples:**

```bash
# Show commit history
$ clony log
commit a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
Author: John Doe <john@example.com>
Date:   Wed Apr 5 12:00:00 2023 +0000

    Add feature X

commit b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1
Author: Jane Smith <jane@example.com>
Date:   Tue Apr 4 10:30:00 2023 +0000

    Initial commit

# Show commit history in a repository with no commits
$ clony log
INFO     No commits found.

# Show commit history outside a git repository
$ clony log
ERROR    Not a git repository. Run 'clony init' to create one.
```

## 💻 Development

Clony is built with a focus on code quality, test coverage, and maintainability. The project follows a modular architecture that makes it easy to extend and enhance.

### Architecture Overview

The codebase is organized into several key modules:

- **Core**: Contains the fundamental Git data structures and operations
  - `objects.py`: Implements Git objects (blobs, trees, commits)
  - `refs.py`: Handles Git references (branches, tags)
  - `repository.py`: Manages Git repositories

- **Internals**: Provides internal utilities for Git operations
  - `commit.py`: Handles commit creation and management
  - `log.py`: Manages the commit history functionality
  - `reset.py`: Implements reset functionality with different modes
  - `staging.py`: Manages the staging area and file staging
  - `status.py`: Manages the working tree status functionality

- **Utils**: Contains utility functions and helpers
  - `logger.py`: Configures logging throughout the application

- **CLI**: The command-line interface (`cli.py`) that ties everything together

### Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/DataRohit/clony.git
cd clony

# Set up virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate    # Linux/Mac

# Install development dependencies
pip install -e ".[dev]"
```

### Code Quality Tools

Clony uses several tools to maintain code quality:

```bash
# Run tests with coverage
pytest -v

# Run linting
ruff check .

# Format code
ruff format .
```

### Automated Checks

For convenience, a script is provided to run both linting and tests in one command:

```bash
# Make the script executable (first time only)
chmod +x run_checks.sh

# Run linting and tests
./run_checks.sh
```

This script will:
1. Run Ruff checks on your code
2. Attempt to fix any issues automatically
3. Run pytest with coverage reporting

It's recommended to run this script after making changes to ensure code quality and test coverage are maintained.

### Contribution Guidelines

Contributions to Clony are welcome! Here are some guidelines to follow:

1. **Fork the repository** and create a new branch for your feature or bug fix
2. **Write tests** for your changes to maintain 100% test coverage
3. **Follow the code style** by running the formatting tools before submitting
4. **Run the automated checks** to ensure your changes pass all tests
5. **Submit a pull request** with a clear description of your changes

### Key Design Principles

- **Modularity**: Each component has a single responsibility
- **Testability**: All code is designed to be easily testable
- **Error Handling**: Robust error handling with informative messages
- **Documentation**: Clear documentation for all functions and modules
- **User Experience**: Focus on providing a clean and intuitive CLI

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](license) file for details.

---

<div align="center">
Made with ❤️ by Rohit Vilas Ingole
</div>