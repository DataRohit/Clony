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

**A modern Git clone tool with a cool CLI interface**

<p>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="Python Version"></a>
  <a href="license"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  <a href="https://pytest-cov.readthedocs.io/"><img src="https://img.shields.io/badge/coverage-100%25-brightgreen" alt="Test Coverage"></a>
</p>

</div>

## ✨ Features

- 🎨 **Modern and visually appealing CLI interface** powered by Rich
- 🔧 **Git repository management** with initialization and configuration
- 📂 **File staging system** with intelligent error handling
- 🧩 **Modular architecture** for easy extensibility
- 📊 **Complete test coverage** (100%) for reliability
- 🚀 **Simple and intuitive commands** for efficient workflow

## 📋 Table of Contents

- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [License](#-license)

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/DataRohit/clony.git
cd clony

# Set up virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -e .
```

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

## 📁 Project Structure

```
clony/
├── clony/                  # Main package
│   ├── __init__.py         # Package initialization with version and exports
│   ├── cli.py              # Command-line interface
│   ├── core/               # Core functionality
│   │   ├── __init__.py     # Core module initialization with exports
│   │   └── repository.py   # Repository management
│   ├── internals/          # Internal utilities
│   │   ├── __init__.py     # Internals module initialization with exports
│   │   └── staging.py      # File staging functionality
│   ├── utils/              # Utility functions
│   │   ├── __init__.py     # Utils module initialization with exports
│   │   └── logger.py       # Logging configuration
│   ├── remote/             # Remote repository operations (future)
│   │   └── __init__.py     # Remote module initialization
│   └── advanced/           # Advanced features (future)
│       └── __init__.py     # Advanced module initialization
├── tests/                  # Test suite
│   ├── __init__.py         # Test package initialization
│   ├── conftest.py         # Pytest configuration
│   ├── test_cli.py         # CLI tests
│   ├── core/               # Tests for core functionality
│   │   ├── __init__.py     # Core tests initialization
│   │   └── test_repository.py  # Repository tests
│   ├── internals/          # Tests for internal utilities
│   │   ├── __init__.py     # Internals tests initialization
│   │   └── test_staging.py # Staging tests
│   └── utils/              # Tests for utility functions
│       ├── __init__.py     # Utils tests initialization
│       └── test_logger.py  # Logger tests
├── pyproject.toml          # Project configuration
├── readme.md               # Project documentation
├── run_checks.sh           # Script to run linting and tests
└── license                 # License information
```

## 💻 Development

Clony is built with a focus on code quality and test coverage:

```bash
# Install development dependencies
pip install -e ".[dev]"

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

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](license) file for details.

---

<div align="center">
Made with ❤️ by Rohit Vilas Ingole
</div>