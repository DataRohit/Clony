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
  <a href="https://pytest-cov.readthedocs.io/"><img src="https://img.shields.io/badge/coverage-95%25%2B-brightgreen" alt="Test Coverage"></a>
</p>

</div>

## ✨ Features

- 🎨 **Modern and visually appealing CLI interface** powered by Rich
- 🔧 **Git repository management** with initialization and configuration
- 🧩 **Modular architecture** for easy extensibility
- 📊 **High test coverage** (95%+) for reliability
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

## 📁 Project Structure

```
clony/
├── __init__.py          # Package initialization and version info
├── cli.py              # Command-line interface using Click and Rich
├── logger.py           # Logging configuration with colorlog
├── repository.py       # Git repository management functionality
├── advanced/          # Reserved for advanced Git operations
│   └── __init__.py
├── core/             # Core Git functionality
│   └── __init__.py
├── internals/        # Internal utilities and helpers
│   └── __init__.py
└── remote/           # Remote repository operations
    └── __init__.py

tests/                # Test suite directory
├── __init__.py
├── test_cli.py       # Tests for CLI functionality
├── test_logger.py    # Tests for logging functionality
└── test_repository.py # Tests for repository operations

# Project Configuration
pyproject.toml        # Project metadata and dependencies
README.md            # Project documentation
LICENSE              # MIT License
```

The project follows a modular structure:
- `cli.py`: Implements the command-line interface using Click and Rich
- `logger.py`: Configures logging with colorlog for better visibility
- `repository.py`: Handles Git repository operations
- `advanced/`: Reserved for advanced Git operations
- `core/`: Contains core Git functionality
- `internals/`: Houses internal utilities and helpers
- `remote/`: Manages remote repository operations
- `tests/`: Contains comprehensive test suite with 95%+ coverage

## 💻 Development

Clony is built with a focus on code quality and test coverage:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest

# Run linting
ruff check .

# Format code
ruff format .
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](license) file for details.

---

<div align="center">
Made with ❤️ by the Rohit Vilas Ingole
</div>
