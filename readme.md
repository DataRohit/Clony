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

Clony provides a modern CLI interface with helpful commands:

```bash
# Display help information
clony --help
clony -h

# Display version information
clony --version
clony -v

# Get help on specific commands
clony help

# Initialize a new Git repository
clony init                     # Initialize in current directory
clony init [path]              # Initialize in specified path
clony init -f                  # Force reinitialization in current directory
clony init -f [path]           # Force reinitialization in specified path
clony init --force             # Force reinitialization in current directory
clony init --force [path]      # Force reinitialization in specified path
```

### Available Commands

#### `init` - Initialize a new Git repository

Creates a Git repository in the specified directory. If no directory is provided, initializes in the current directory.

Options:
- `--force, -f`: Force reinitialization of the repository if it already exists
- `--help, -h`: Show help message for the init command

Example:
```bash
# Initialize in current directory
clony init

# Initialize in specific directory
clony init /path/to/repo

# Force reinitialization
clony init --force
```

### Example Output

When you run `clony --help`, you'll see a beautifully formatted help screen:

```
╭─────────────────────────────────── A Modern Git Clone Tool ───────────────────────────────────╮
│                                                                                               │
│                                                                                               │
│      ██████╗██╗      ██████╗ ███╗   ██╗██╗   ██╗                                              │
│     ██╔════╝██║     ██╔═══██╗████╗  ██║╚██╗ ██╔╝                                              │
│     ██║     ██║     ██║   ██║██╔██╗ ██║ ╚████╔╝                                               │
│     ██║     ██║     ██║   ██║██║╚██╗██║  ╚██╔╝                                                │
│     ╚██████╗███████╗╚██████╔╝██║ ╚████║   ██║                                                 │
│      ╚═════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝                                                 │
│                                                                                               │
│                                                                                               │
╰─────────────────────────────────────────── v0.1.0 ────────────────────────────────────────────╯
╭───────────────────────────────────────── Description ─────────────────────────────────────────╮
│                                                                                               │
│  Clony: A modern Git clone tool with a cool CLI interface.                                    │
│                                                                                               │
│  Run 'clony --help' for usage information.                                                    │
│                                                                                               │
╰───────────────────────────────────────────────────────────────────────────────────────────────╯
                   Commands
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Command ┃ Description                      ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ help    │ Show this help message and exit. │
└─────────┴──────────────────────────────────┘
                      Options
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Option        ┃ Description                      ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ --help, -h    │ Show this help message and exit. │
│ --version, -v │ Show the version and exit.       │
└───────────────┴──────────────────────────────────┘
╭──────────────────────────────────────────── Usage ────────────────────────────────────────────╮
│ clony [OPTIONS] COMMAND [ARGS]...                                                             │
╰───────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 📁 Project Structure

```
clony/
├── clony/                  # Main package
│   ├── __init__.py         # Package initialization
│   ├── cli.py              # Command-line interface
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
