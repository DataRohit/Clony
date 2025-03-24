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
- 🌿 **Branch management** with create, list, and delete operations
- 🧩 **Modular architecture** for easy extensibility
- 📊 **100% test coverage** ensuring reliability
- 🚀 **Intuitive commands** with consistent syntax
- 🛡️ **Clear error handling** with actionable messages
- 📝 **Detailed logging** for debugging operations
- 🔍 **Transparent internals** for educational purposes

## 📋 Table of Contents

- [Installation](#-installation)
  - [Prerequisites](#prerequisites)
  - [Installation Steps](#installation-steps)
  - [Installing for Development](#installing-for-development)
  - [Troubleshooting](#troubleshooting)
- [Usage](#-usage)
  - [Available Commands](#available-commands)
    - [Global Options](#global-options)
    - [help](#help)
    - [init](#init)
    - [stage](#stage)
    - [commit](#commit)
    - [status](#status)
    - [log](#log)
    - [blobs](#blobs)
    - [diff](#diff)
    - [reset](#reset)
    - [branch](#branch)
    - [checkout](#checkout)
    - [merge](#merge)
- [Development](#-development)
  - [Architecture Overview](#architecture-overview)
  - [Development Environment Setup](#development-environment-setup)
  - [Code Quality Tools](#code-quality-tools)
  - [Automated Checks](#automated-checks)
  - [Contribution Guidelines](#contribution-guidelines)
  - [Key Design Principles](#key-design-principles)
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
clony init [path]  # Create a new Git repository in the specified path (default: current directory)

# Options
--force, -f       # Force reinitialization if repository already exists
--help, -h        # Show help for init command
```

**Examples:**

```bash
# Initialize in current directory
$ clony init
[03/19/25 22:42:21] INFO     Git repository initialized successfully
                    INFO     Initialized empty Git repository in D:\Projects\test_repo

# Initialize in a specific directory that already exists
$ clony init my-project
[03/19/25 22:32:15] INFO     Git repository initialized successfully
                    INFO     Initialized empty Git repository in /path/to/my-project

# Initialize in a new directory (creates the directory automatically)
$ clony init new-project
[03/19/25 22:32:24] INFO     Git repository initialized successfully
                    INFO     Initialized empty Git repository in /path/to/new-project

# Try to initialize in existing repository
$ clony init existing-repo
[03/19/25 22:32:33] WARNING  Git repository already exists
                    INFO     Use --force to reinitialize

# Force reinitialization of an existing repository
$ clony init existing-repo --force
[03/19/25 22:32:42] INFO     Git repository initialized successfully
                    INFO     Initialized empty Git repository in /path/to/existing-repo

# Initialize with invalid path (non-existent parent directory)
$ clony init /invalid/path
[03/19/25 22:32:51] ERROR    Parent directory does not exist: /invalid/path

# Initialize with relative path
$ clony init ../sibling-project
[03/19/25 22:33:00] INFO     Git repository initialized successfully
                    INFO     Initialized empty Git repository in /path/to/sibling-project
```

The `init` command creates the standard Git directory structure including:
- `.git` directory with all required subdirectories
- `objects` directory for Git object storage
- `refs` directory with `heads` and `tags` subdirectories
- Default `HEAD` file pointing to the `main` branch
- Basic Git configuration file

When initializing a repository, Clony performs several checks to ensure the operation will succeed:
1. Verifies the parent directory exists
2. Checks if a Git repository already exists at the location
3. Creates all required directories and files with proper permissions

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
$ clony stage test1.txt
[03/19/25 22:42:43] INFO     File staged: 'test1.txt'

           Staging Results           
┏━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ File Path ┃ Status ┃ Content Hash ┃
┡━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│ test1.txt │ STAGED │ bb52363e     │
└───────────┴────────┴──────────────┘

# Try to stage a non-existent file
$ clony stage non_existent_file.txt
[03/19/25 22:35:20] ERROR    File not found: 'non_existent_file.txt'

# Stage a file in a non-git repository
$ clony stage file_outside_repo.txt
[03/19/25 22:35:35] ERROR    Not a git repository. Run 'clony init' to create one.

# Try to stage a file that's already staged with no changes
$ clony stage already_staged.txt
[03/19/25 22:35:45] WARNING  File already staged: 'already_staged.txt'

           Staging Results           
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ File Path       ┃ Status    ┃ Content Hash ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ already_staged.txt│ UNCHANGED │ e5f6g7h8    │
└──────────────────┴───────────┴──────────────┘

# Stage a file after changing its content
$ echo "Changed content" > myfile.txt
$ clony stage myfile.txt
[03/19/25 22:36:05] INFO     File staged: 'myfile.txt'

           Staging Results           
┏━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ File Path ┃ Status ┃ Content Hash ┃
┡━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│ myfile.txt│ STAGED │ b2c3d4e5     │
└───────────┴────────┴──────────────┘

# Try to stage a file with invalid path
$ clony stage /invalid/path/file.txt
[03/19/25 22:36:15] ERROR    File not found: '/invalid/path/file.txt'

# Stage multiple files sequentially
$ clony stage file1.txt
[03/19/25 22:37:25] INFO     File staged: 'file1.txt'

           Staging Results           
┏━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ File Path ┃ Status ┃ Content Hash ┃
┡━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│ file1.txt │ STAGED │ h8i9j0k1     │
└───────────┴────────┴──────────────┘

$ clony stage file2.txt
[03/19/25 22:42:54] INFO     File staged: 'file2.txt'

           Staging Results           
┏━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ File Path ┃ Status ┃ Content Hash ┃
┡━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│ file2.txt │ STAGED │ ac43975e     │
└───────────┴────────┴──────────────┘
```

The staging process performs several key operations:
1. Calculates a SHA-1 hash of the file content
2. Compresses the content using zlib
3. Stores the compressed content in the Git object database
4. Updates the index file with the file path and hash
5. Prevents staging unchanged files to avoid empty commits

After staging, you can use the `status` command to see all staged files, and then create a commit with the `commit` command.

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
$ clony commit --message "Initial commit with test files"
                               Commit Information                               
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Commit Hash ┃ Author                        ┃ Message                        ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ b68a0ef     │ Clony User                    │ Initial commit with test files │
└─────────────┴───────────────────━━━─────────┴────────────────────────────────┘

# Create a commit with author information
$ clony commit --message "Add feature" --author-name "John Doe" --author-email "john@example.com"
                        Commit Information                      
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Commit Hash ┃ Author                     ┃ Message     ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ e4f5g6h     │ John Doe <john@example.com>│ Add feature │
└─────────────┴────────────────────────────┴─────────────┘

# Commit with a longer descriptive message
$ clony commit --message "Update test1.txt"
                        Commit Information                        
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Commit Hash ┃ Author                        ┃ Message          ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ b6a6cba     │ Clony User                    │ Update test1.txt │
└─────────────┴───────────────────━━━─────────┴──────────────────┘

# Try to commit without a message
$ clony commit
[03/19/25 22:38:35] ERROR    Missing option '--message' / '-m'.

# Try to commit with no staged changes
$ clony commit --message "Empty commit"
[03/19/25 22:38:45] ERROR    Nothing to commit. Run 'clony stage <file>' to stage changes.

# Try to commit outside a git repository
$ clony commit --message "Outside repo"
[03/19/25 22:38:55] ERROR    Not a git repository. Run 'clony init' to create one.
```

The commit process performs several key operations:
1. Creates a tree object representing the directory structure
2. Gets the current HEAD commit as the parent
3. Creates a commit object with the tree, parent, author info, and message
4. Updates the branch reference to point to the new commit
5. Updates the HEAD_TREE file to track all committed files 
6. Clears the staging area for the next set of changes

After creating a commit, you can use the `log` command to view the commit history, and `status` to confirm the staging area is cleared.

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
# Show status with staged files
$ clony status
[03/19/25 22:42:49] INFO     On branch main
                    INFO     Use 'clony reset HEAD <file>...' to unstage
Changes to be committed 
┏━━━━━━━━━━━┳━━━━━━━━━━┓
┃ File      ┃ Status   ┃
┡━━━━━━━━━━━╇━━━━━━━━━━┩
│ test1.txt │ New file │
└───────────┴──────────┘
                    INFO     Use 'clony stage <file>...' to include in what will be committed
  Untracked  
    files    
┏━━━━━━━━━━━┓
┃ File      ┃
┡━━━━━━━━━━━┩
│ test2.txt │
└───────────┘

# Show status after committing all files (clean working tree)
$ clony status
[03/19/25 22:43:15] INFO     On branch main
                    INFO     Nothing to commit, working tree clean

# Show status after modifying a committed file
$ echo "Modified content" > test1.txt
$ clony status
[03/19/25 22:43:30] INFO     On branch main
                    INFO     Use 'clony stage <file>...' to update what will be committed
  Changes not   
staged for commit
┏━━━━━━━━━━━┳━━━━━━━━━━┓
┃ File      ┃ Status   ┃
┡━━━━━━━━━━━╇━━━━━━━━━━┩
│ test1.txt │ Modified │
└───────────┴──────────┘

# Show status in a non-git repository
$ clony status /not/a/repo
[03/19/25 22:43:45] ERROR    Not a git repository. Run 'clony init' to create one.
```

The status command performs several operations:
1. Checks if you're in a Git repository
2. Determines the current branch
3. Reads the index file to find staged changes
4. Compares working directory files with the HEAD commit to find unstaged changes
5. Identifies untracked files in the working directory
6. Displays all findings in a clear, organized tabular format

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
                                             Commit History

┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Commit Hash             ┃ Author                  ┃ Date                    ┃ Message                 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ b6a6cbaf9e123456789abc… │ Clony User              │ Wed Mar 19 22:45:00     │ Update test1.txt        │
│                         │ <user@example.com>      │ 2025 +0530              │                         │
└─────────────────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┘
│ b68a0efae1cd79937eb746… │ Clony User              │ Wed Mar 19 22:43:00     │ Initial commit with     │
│                         │ <user@example.com>      │ 2025 +0530              │ test files              │
└─────────────────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┘

# Show commit history in a repository with no commits
$ clony log
[03/19/25 22:45:30] INFO     No commits found.

# Show commit history outside a git repository
$ clony log
[03/19/25 22:45:45] ERROR    Not a git repository. Run 'clony init' to create one.
```

The log command performs several operations:
1. Reads the HEAD reference to find the current branch
2. Traverses the commit graph from the most recent commit
3. Parses each commit object to extract metadata (author, date, message)
4. Formats the commit history in a clean tabular display
5. Handles edge cases like empty repositories or detached HEAD states

#### `blobs`

Display all blob hashes from a specified commit. This command retrieves and displays all blob hashes associated with files in the specified commit's tree.

```bash
# Basic Usage
clony blobs <commit>  # Display all blob hashes from the specified commit

# Options
--help, -h          # Show help for blobs command
```

**Examples:**

```bash
# Show blobs from the main branch
$ clony blobs main
             Blob Hashes in Commit b68a0efa             
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Blob Hash                                ┃ File Path ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 9f4b6d8bfeaf44aaa69872286163784706d1b053 │ test1.txt │
│ ac439756c6fb3ee361bd0126ad6cdf9ffde9ec2c │ test2.txt │
└──────────────────────────────────────────┴───────────┘

# Show blobs from a specific commit hash
$ clony blobs b6a6cbaf
             Blob Hashes in Commit b6a6cbaf             
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Blob Hash                                ┃ File Path ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ f776a8f3bf069022eedc67803f8d40043fa56324 │ test1.txt │
│ ac439756c6fb3ee361bd0126ad6cdf9ffde9ec2c │ test2.txt │
└──────────────────────────────────────────┴───────────┘

# Try to get blobs from an invalid commit reference
$ clony blobs HEAD
[03/19/25 22:45:21] ERROR    Invalid commit reference: HEAD

# Try to get blobs outside a git repository
$ clony blobs main
[03/19/25 22:46:15] ERROR    Not a git repository. Run 'clony init' to create one.
```

The blobs command performs several operations:
1. Resolves the commit reference (branch, tag, or commit hash)
2. Reads the commit object to find the root tree
3. Traverses the tree recursively to find all blob objects
4. Displays the blob hashes and their associated file paths in a table
5. Handles errors such as invalid commit references

#### `diff`

Display the differences between two blob objects. This command compares the contents of two blob objects and shows the differences between them line by line.

```bash
# Basic Usage
clony diff <blob1> <blob2>  # Compare two blob objects

# Options
--path1 TEXT             # The path of the first file
--path2 TEXT             # The path of the second file
--algorithm TEXT         # The diff algorithm to use (myers or unified)
--context-lines INTEGER  # The number of context lines to show in the unified diff
--help, -h               # Show help for diff command
```

**Examples:**

```bash
# Compare two blob objects using their hashes
$ clony diff 9f4b6d8bfeaf44aaa69872286163784706d1b053 f776a8f3bf069022eedc67803f8d40043fa56324
- This is a test file
+ This is an updated test file

# Compare with paths and algorithm specified
$ clony diff 9f4b6d8bfeaf44aaa69872286163784706d1b053 f776a8f3bf069022eedc67803f8d40043fa56324 --path1 test1.txt --path2 test1.txt --algorithm unified
--- test1.txt
+++ test1.txt
@@ -1 +1 @@
-This is a test file
+This is an updated test file

# Try to use the diff command with only one blob hash
$ clony diff 9f4b6d8bfeaf44aaa69872286163784706d1b053
[03/19/25 22:47:15] ERROR    Missing argument 'BLOB2'.

# Try to use diff outside a git repository
$ clony diff blob1 blob2
[03/19/25 22:47:30] ERROR    Not a git repository. Run 'clony init' to create one.
```

The diff command performs several operations:
1. Reads the content of both blob objects from the Git object database
2. Parses the content of each blob
3. Compares the content line by line using the specified algorithm
4. Displays the differences in a clear, standardized format
5. Handles various output formats based on the selected options

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
$ clony reset b68a0efae1cd79937eb7466065db7fbd5dc4969a
                      Reset Results
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Commit Hash ┃ Reset Mode ┃ Actions Taken              ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ b68a0efa    │ MIXED      │ • HEAD pointer updated     │
│             │            │ • Index/staging area reset │
└─────────────┴────────────┴────────────────────────────┘
                        Commit Details
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property  ┃ Value                                          ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Tree      │ 99f1d991447efa7c2455a7df54845d2b4b53e6dc       │
│ Parent    │                                                │
│ Author    │ Clony User <user@example.com> 1742404380 +0530 │
│ Committer │ Clony User <user@example.com> 1742404380 +0530 │
│ Message   │ Initial commit with test files                 │
└───────────┴────────────────────────────────────────────────┘

# Perform a soft reset
$ clony reset --soft b68a0efa
                      Reset Results
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Commit Hash ┃ Reset Mode ┃ Actions Taken          ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ b68a0efa    │ SOFT       │ • HEAD pointer updated │
└─────────────┴────────────┴─────────────━━━────────┘
                        Commit Details
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property  ┃ Value                                          ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Tree      │ 99f1d991447efa7c2455a7df54845d2b4b53e6dc       │
│ Parent    │                                                │
│ Author    │ Clony User <user@example.com> 1742404380 +0530 │
│ Committer │ Clony User <user@example.com> 1742404380 +0530 │
│ Message   │ Initial commit with test files                 │
└───────────┴────────────────────────────────────────────────┘

# Perform a hard reset
$ clony reset --hard b68a0efa
                      Reset Results
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Commit Hash ┃ Reset Mode ┃ Actions Taken                  ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ b68a0efa    │ HARD       │ • HEAD pointer updated         │
│             │            │ • Index/staging area reset     │
│             │            │ • Working directory updated    │
└─────────────┴────────────┴────────────────────────────────┘
                        Commit Details
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property  ┃ Value                                          ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Tree      │ 99f1d991447efa7c2455a7df54845d2b4b53e6dc       │
│ Parent    │                                                │
│ Author    │ Clony User <user@example.com> 1742404380 +0530 │
│ Committer │ Clony User <user@example.com> 1742404380 +0530 │
│ Message   │ Initial commit with test files                 │
└───────────┴────────────────────────────────────────────────┘

# Reset to a branch name
$ clony reset main
                      Reset Results
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Commit Hash ┃ Reset Mode ┃ Actions Taken              ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ b6a6cba     │ MIXED      │ • HEAD pointer updated     │
│             │            │ • Index/staging area reset │
└─────────────┴────────────┴────────────────────────────┘
                        Commit Details
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property  ┃ Value                                          ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Tree      │ 2a51f3ebb69151c2a11aad6709dc448ef9e8c66b       │
│ Parent    │ b68a0efae1cd79937eb7466065db7fbd5dc4969a       │
│ Author    │ Clony User <user@example.com> 1742404420 +0530 │
│ Committer │ Clony User <user@example.com> 1742404420 +0530 │
│ Message   │ Update test1.txt                               │
└───────────┴────────────────────────────────────────────────┘

# Try to reset with an invalid commit reference
$ clony reset invalid-commit
[03/19/25 22:49:15] ERROR    Failed to reset HEAD to invalid-commit: Not a valid commit reference

# Try to reset outside a git repository
$ clony reset b68a0efa
[03/19/25 22:49:30] ERROR    Not in a Git repository
```

The reset command performs several operations depending on the mode:
1. Resolves the commit reference to a specific commit hash
2. Updates the HEAD reference to point to the new commit
3. In mixed and hard modes, updates the index to match the commit's tree
4. In hard mode, updates the working directory to match the commit's tree
5. Provides detailed output about the actions taken during the reset
6. Shows information about the commit you've reset to
7. Handles errors such as invalid commit references or repository issues

#### `branch`

Create a new branch in the repository. This command creates a new branch pointing to the specified commit or the current HEAD if no commit is specified.

```bash
# Basic Usage
clony branch <branch_name>  # Create a new branch pointing to HEAD
clony branch <branch_name> --commit <commit_hash>  # Create a branch pointing to a specific commit
clony branch <branch_name> --delete  # Delete a branch
clony branch <branch_name> --delete --force  # Force delete a branch
clony branch --list  # List all branches in the repository

# Options
--commit TEXT        # The commit hash to point the branch to (default: HEAD)
--delete, -d        # Delete the specified branch
--force, -f         # Force operation (such as deleting current branch)
--list, -l          # List all branches in the repository
--help, -h          # Show help for branch command
```

**Examples:**

```bash
# Create a new branch pointing to HEAD
$ clony branch feature-branch
[03/20/25 18:26:32] INFO     Created branch 'feature-branch' pointing to
                             1cf1a49fed25e8cd86109dd61e009c9ab5c4f510

# Create a branch pointing to a specific commit
$ clony branch old-branch --commit b68a0efa
[03/20/25 18:26:35] INFO     Created branch 'old-branch' pointing to
                             b68a0efae1cd79937eb7466065db7fbd5dc4969a

# Try to create a branch with invalid commit
$ clony branch invalid-branch --commit invalid-hash
[03/20/25 18:26:38] ERROR    Invalid commit reference: invalid-hash

# Delete a branch
$ clony branch feature-branch --delete
[03/20/25 18:27:06] INFO     Deleted branch: feature-branch

# Try to delete the current branch
$ clony branch main --delete
[03/20/25 18:27:02] ERROR    Cannot delete the current branch: main

# Force delete the current branch
$ clony branch main --delete --force
[03/20/25 18:27:10] INFO     Force deleted current branch: main

# List all branches
$ clony branch --list
          Branches          
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Current ┃ Branch         ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│         │ feature-branch │
│    ✓    │ main           │
└─────────┴────────────────┘
```

#### `checkout`

Checkout a branch, commit, or restore files. This command has two main functionalities:

1. **Branch/Commit Checkout**: Updates the HEAD, index, and working directory to match the state of the specified branch or commit.
2. **File Restoration**: Restores specific files from a branch or commit without changing the current branch.

```bash
# Basic Usage
clony checkout <target>  # Checkout a branch or commit
clony checkout <target> <file_paths>...  # Restore specific files from a branch or commit

# Options
--force, -f           # Force checkout even if there are uncommitted changes
--help, -h            # Show help for checkout command
```

**Examples:**

```bash
# Checkout a branch
$ clony checkout feature-branch
Checking out feature-branch
                    Checkout Results                    
┏━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Target         ┃ Type   ┃ HEAD State ┃ Files Updated ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ feature-branch │ Branch │ Attached   │ 3             │
└────────────────┴────────┴────────────┴───────────────┘

# Checkout a commit (detached HEAD)
$ clony checkout d2c4431
Checking out d2c4431
                Checkout Results                 
┏━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Target  ┃ Type   ┃ HEAD State ┃ Files Updated ┃
┡━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ d2c4431 │ Commit │ Detached   │ 3             │
└─────────┴────────┴────────────┴───────────────┘

# Checkout will fail if there are uncommitted changes
$ clony checkout main
Checking out main
                Checkout Conflicts                
┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ File      ┃ Status   ┃ Action Required         ┃
┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ file1.txt │ Modified │ Commit or stash changes │
└───────────┴──────────┴─────────────────────────┘
Checkout failed.

# Force checkout to overwrite uncommitted changes
$ clony checkout main --force
Checking out main
                Checkout Results                
┏━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Target ┃ Type   ┃ HEAD State ┃ Files Updated ┃
┡━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ main   │ Branch │ Attached   │ 3             │
└────────┴────────┴────────────┴───────────────┘

# Restore a specific file from a commit
$ clony checkout 9efa21c file1.txt
Restoring file 'file1.txt' from 9efa21c
Restored 1 file(s) from 9efa21c

# Restore will fail if there are local modifications
$ clony checkout 9efa21c file1.txt
Restoring file 'file1.txt' from 9efa21c
                Checkout Conflicts                
┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ File      ┃ Status   ┃ Action Required         ┃
┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ file1.txt │ Modified │ Commit or stash changes │
└───────────┴──────────┴─────────────────────────┘
Failed to restore files.

# Force restore to overwrite local modifications
$ clony checkout 9efa21c file1.txt --force
Restoring file 'file1.txt' from 9efa21c
Restored 1 file(s) from 9efa21c
```

The checkout command performs several key operations:
1. For branch/commit checkout:
   - Updates HEAD to point to the branch or commit
   - Updates the index (staging area) to match the tree
   - Updates the working directory files
   - Provides a warning when entering a detached HEAD state

2. For file restoration:
   - Extracts the specified files from the target commit/branch
   - Updates only those files in the working directory
   - Preserves the current branch and HEAD state
   - Detects conflicts with local modifications

The `--force` flag overrides conflict detection and allows the command to proceed even when uncommitted changes would be lost. Use this option with caution as it can lead to data loss.

#### `merge`

Perform a three-way merge with the current branch. This command merges changes from a specified commit into the current branch, using an explicitly provided base commit as the common ancestor.

Unlike standard Git which automatically finds the common ancestor, Clony requires you to manually specify both the base commit and the commit to be merged.

```bash
# Basic Usage
clony merge <base> <other>  # Merge changes from OTHER into current branch, with BASE as common ancestor

# Options
--help, -h          # Show help for merge command
```

**Examples:**

```bash
# Merge a feature branch into the current branch
$ clony merge 9dccc5d fc16929
[03/24/25 16:38:12] INFO     Merge completed successfully with no conflicts.

# Merge with conflicts
$ clony merge base_commit feature_branch
[03/24/25 16:39:15] WARNING  Merge completed with 2 conflict(s). Manual resolution required.
            Merge Results            
┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ File      ┃ Status   ┃ Conflicts  ┃
┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━┩
│ test1.txt │ Conflicts│ 1          │
│ test2.txt │ Conflicts│ 1          │
└───────────┴──────────┴────────────┘

Conflicts were found during the merge:

File: test1.txt
┏━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Line ┃ This Branch   ┃ Other Branch         ┃
┡━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ 3    │ This line     │ Different line       │
└──────┴───────────────┴──────────────────────┘

# Try to merge with invalid base commit
$ clony merge invalid_base feature_branch
[03/24/25 16:40:30] ERROR    Invalid base commit: invalid_base

# Try to merge with invalid other commit
$ clony merge base_commit invalid_other
[03/24/25 16:40:45] ERROR    Invalid other commit: invalid_other

# Try to merge outside a git repository
$ clony merge base_commit other_commit
[03/24/25 16:41:00] ERROR    Not a git repository. Run 'clony init' to create one.
```

The merge command performs several key operations:
1. Validates both the base and other commit references
2. Identifies the current branch's HEAD commit
3. Performs a three-way merge between base, HEAD, and other commits
4. Detects conflicts when the same lines are modified differently
5. Displays merge results in a clean, formatted table
6. Shows detailed conflict information when conflicts are found

The key difference from standard Git is that Clony requires you to explicitly specify the base commit (common ancestor), while Git automatically computes this. This gives you more control but requires more knowledge of your repository's commit history.

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
  - `branch.py`: Handles branch creation, listing, and deletion

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