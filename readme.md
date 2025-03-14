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
File staged: 'myfile.txt'

# Try to stage a non-existent file
$ clony stage non_existent_file.txt
ERROR    File not found: 'non_existent_file.txt'

# Stage a file in a non-git repository
$ clony stage file_outside_repo.txt
ERROR    Not a git repository

# Try to stage a file that's already staged
$ clony stage already_staged.txt
WARNING  File already staged: 'file01.txt'

# Stage a file after changing its content
$ echo "Changed content" > myfile.txt
$ clony stage myfile.txt
File staged: 'myfile.txt'

# Stage a file with invalid path
$ clony stage /invalid/path/file.txt
ERROR    File not found: '/invalid/path/file.txt'
```

## 📁 Project Structure

```
clony/
├── clony/                  # Main package
│   ├── __init__.py         # Package initialization
│   ├── cli.py              # Command-line interface
│   ├── staging.py          # File staging functionality
│   ├── repository.py       # Repository management
│   ├── logger.py           # Logging configuration
│   ├── core/               # Core functionality
│   │   └── __init__.py
│   ├── remote/             # Remote repository operations
│   │   └── __init__.py
│   ├── advanced/           # Advanced features
│   │   └── __init__.py
│   └── internals/          # Internal utilities
│       └── __init__.py
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Test configuration
│   └── test_cli.py         # CLI tests
├── pyproject.toml          # Project configuration
├── README.md               # Project documentation
└── LICENSE                 # License information
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

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](license) file for details.

---

<div align="center">
Made with ❤️ by Rohit Vilas Ingole
</div>