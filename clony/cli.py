"""
CLI module for Clony.

This module provides the command-line interface for the Clony Git clone tool.
"""

# Standard imports
import pathlib
import sys

# Third-party imports
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Local imports
from clony import __version__
from clony.core.diff import print_diff, read_git_object
from clony.core.objects import parse_tree_object
from clony.core.refs import (
    create_branch,
    delete_branch,
    get_current_branch,
    list_branches,
)
from clony.core.repository import Repository
from clony.internals.checkout import restore_files, switch_branch_or_commit
from clony.internals.commit import make_commit
from clony.internals.log import display_commit_logs, parse_commit_object
from clony.internals.merge import perform_merge
from clony.internals.reset import reset_head, validate_commit_reference
from clony.internals.staging import stage_file
from clony.internals.status import get_status
from clony.utils.logger import logger

# Initialize rich console for pretty output
console = Console()


# Function to display the Clony logo
def display_logo():
    """
    Display the Clony logo in the terminal.
    """

    # Get the logo text
    logo_text = """
    ██████╗██╗      ██████╗ ███╗   ██╗██╗   ██╗
   ██╔════╝██║     ██╔═══██╗████╗  ██║╚██╗ ██╔╝
   ██║     ██║     ██║   ██║██╔██╗ ██║ ╚████╔╝
   ██║     ██║     ██║   ██║██║╚██╗██║  ╚██╔╝
   ╚██████╗███████╗╚██████╔╝██║ ╚████║   ██║
    ╚═════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝
    """

    # Display the logo
    logo = Text(logo_text)
    logo.stylize("bold cyan")

    # Create a panel for the logo
    panel = Panel(
        logo,
        title="[bold green]A Modern Git Clone Tool[/bold green]",
        subtitle=f"[bold blue]v{__version__}[/bold blue]",
        border_style="green",
        padding=(1, 2),
    )

    # Print the panel
    console.print(panel)


# Function to display stylized help
def display_stylized_help(ctx, show_logo=True):
    """
    Display a stylized help message using Rich.

    Args:
        ctx: The Click context object.
        show_logo: Whether to display the logo. Defaults to True.
    """

    # Display the logo first if requested
    if show_logo:
        display_logo()

    # Create a panel for the description
    description = ctx.command.help or "No description available."
    desc_panel = Panel(
        Markdown(description),
        title="[bold yellow]Description[/bold yellow]",
        border_style="yellow",
    )
    console.print(desc_panel)

    # Create a table for the commands (if any)
    if hasattr(ctx.command, "commands") and ctx.command.commands:
        cmd_table = Table(title="[bold blue]Commands[/bold blue]", border_style="blue")
        cmd_table.add_column("Command", style="cyan")
        cmd_table.add_column("Description", style="green")

        # Add the commands to the table
        for cmd_name, cmd in sorted(ctx.command.commands.items()):
            # Get the first line of the help text
            cmd_help = cmd.help or "No description available."
            first_line = cmd_help.split("\n")[0].strip()
            cmd_table.add_row(cmd_name, first_line)

        # Print the table
        console.print(cmd_table)

    # Create a table for the options
    if ctx.command.params:
        opt_table = Table(
            title="[bold magenta]Options[/bold magenta]", border_style="magenta"
        )
        opt_table.add_column("Option", style="cyan")
        opt_table.add_column("Description", style="green")

        # Add the options to the table
        for param in ctx.command.params:
            # Format the option names
            opts = []
            for opt in param.opts:
                opts.append(opt)
            for opt in param.secondary_opts:
                opts.append(opt)
            opt_str = ", ".join(opts)

            # Get the help text
            help_text = param.help or "No description available."

            # Add the option to the table
            opt_table.add_row(opt_str, help_text)

        # Print the table
        console.print(opt_table)

    # Add usage example
    usage_panel = Panel(
        "[bold]clony [OPTIONS] COMMAND [ARGS]...[/bold]",
        title="[bold cyan]Usage[/bold cyan]",
        border_style="cyan",
    )
    console.print(usage_panel)


# Create a custom Click context settings to enable -h as a help shorthand
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


# Custom help option to override Click's default help
@click.command(add_help_option=False, name="help")
@click.pass_context
def help_command(ctx):
    """Show this help message and exit."""
    # Display the help message
    display_stylized_help(ctx.parent, show_logo=False)

    # Exit the program
    sys.exit(0)


# Main CLI group
@click.group(
    invoke_without_command=True,
    context_settings=CONTEXT_SETTINGS,
    add_help_option=False,
)
@click.option("--help", "-h", is_flag=True, help="Show this help message and exit.")
@click.option("--version", "-v", is_flag=True, help="Show the version and exit.")
@click.pass_context
def cli(ctx, help, version):
    """
    Clony: A modern Git clone tool with a colorful CLI interface.

    Run 'clony --help' for usage information.
    """

    # Store the context for later use
    ctx.obj = {}

    # If help was requested
    if help:
        # Display the help message
        display_stylized_help(ctx)

        # Exit the program
        sys.exit(0)

    # Display the logo only when no subcommand is invoked or help/version is requested
    if ctx.invoked_subcommand is None and not help and not version:
        display_logo()

    # If no command is provided or --version is specified
    if ctx.invoked_subcommand is None or version:
        # Display the version if requested
        if version:
            version_text = "[bold cyan]Clony[/bold cyan] version: "
            version_text += f"[bold green]{__version__}[/bold green]"
            console.print(version_text)

        # Show help if no command is provided
        elif ctx.invoked_subcommand is None:
            display_stylized_help(ctx, show_logo=False)

        # Exit the program
        sys.exit(0)


# Add the help command to the CLI
cli.add_command(help_command)


# Function to serve as the entry point for the CLI
def main():
    """
    Main entry point for the Clony CLI.
    """

    try:
        # Run the CLI
        cli()
    except Exception as e:
        # Log the error and exit
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


# Execute the CLI if this file is run directly
if __name__ == "__main__":  # pragma: no cover
    # Run the CLI
    main()


# Initialize a new Git repository
@cli.command()
@click.argument("path", type=click.Path(), default=".")
@click.option(
    "--force", "-f", is_flag=True, help="Force reinitialization of the repository."
)
def init(path: str, force: bool):
    """Initialize a new Git repository in the specified directory.

    Creates a Git repository in the specified directory. If no directory is
    provided, initializes in the current directory.
    """

    # Convert the path to an absolute path
    repo_path = pathlib.Path(path).resolve()

    # Create a new repository instance
    repo = Repository(str(repo_path))

    # Initialize the repository
    if repo.init(force=force):
        logger.info(f"Initialized empty Git repository in {repo_path}")
    else:
        if repo.exists():
            logger.warning("Git repository already exists")
            logger.info("Use --force to reinitialize")
        else:
            logger.error("Failed to initialize Git repository")
        sys.exit(1)


# Stage command to add file content to the staging area
@cli.command()
@click.argument("path", type=click.Path())
def stage(path: str):
    """Stage a file by adding its content to the staging area.

    This command prepares a file to be included in the next commit by
    creating a blob object from the file content and updating the index.
    """
    try:
        # Check if file exists before proceeding
        if not pathlib.Path(path).exists():
            # Log the error and exit
            logger.error(f"File not found: '{path}'")
            sys.exit(1)

        # Stage the file using the staging module
        stage_file(path)
    except Exception as e:
        # Log the error and exit
        logger.error(f"Error staging file: {str(e)}")
        sys.exit(1)


# Commit command to create a new commit with staged changes
@cli.command()
@click.option("--message", "-m", required=True, help="The commit message.")
@click.option("--author-name", default=None, help="The name of the author.")
@click.option("--author-email", default=None, help="The email of the author.")
def commit(message: str, author_name: str, author_email: str):
    """Create a new commit with the staged changes.

    This command creates a new commit object with the staged changes,
    including a tree object representing the directory structure and
    a reference to the parent commit.
    """

    try:
        # Set default author name and email if not provided
        if not author_name:
            author_name = "Clony User"
        if not author_email:
            author_email = "user@example.com"

        # Create the commit using the commit module
        make_commit(message, author_name, author_email)
    except Exception as e:
        # Log the error and exit
        logger.error(f"Error creating commit: {str(e)}")
        sys.exit(1)


# Status command to show the working tree status
@cli.command()
@click.argument("path", type=click.Path(), default=".")
def status(path: str):
    """Show the working tree status.

    This command displays the state of the working directory and the staging area
    in a formatted tabular output. It shows which changes have been staged,
    which haven't, and which files aren't being tracked by Git.
    """

    try:
        # Get the status of the repository
        status_dict, _ = get_status(path)

        # Display the branch information
        logger.info("On branch main")

        # Display the status information in tabular format
        from clony.internals.status import display_status_info

        display_status_info(status_dict)

    except Exception as e:
        # Log the error and exit
        logger.error(f"Error showing status: {str(e)}")
        sys.exit(1)


# Reset command to move HEAD to the specified state
@cli.command()
@click.argument("commit", required=True)
@click.option(
    "--soft",
    is_flag=True,
    help="Move HEAD to the specified commit without changing the index or "
    "working directory.",
)
@click.option(
    "--mixed",
    is_flag=True,
    help="Move HEAD to the specified commit and update the index, but not the "
    "working directory. This is the default.",
)
@click.option(
    "--hard",
    is_flag=True,
    help="Move HEAD to the specified commit and update both the index and "
    "working directory.",
)
def reset(commit: str, soft: bool, mixed: bool, hard: bool):
    """Reset the current HEAD to the specified state.

    This command updates the HEAD to point to the specified commit, and optionally
    updates the index and working directory to match.
    """

    try:
        # Determine the reset mode
        if soft:
            mode = "soft"
        elif hard:
            mode = "hard"
        else:
            # Default to mixed mode
            mode = "mixed"

        # Perform the reset
        if not reset_head(commit, mode):
            # If reset_head returns False, it will have already logged the error
            sys.exit(1)
    except Exception as e:
        # Log the error and exit
        logger.error(f"Error performing reset: {str(e)}")
        sys.exit(1)


# Log command to display commit history
@cli.command()
def log():
    """Display the commit history.

    This command displays the commit history starting from HEAD, showing commit
    hash, author, date, and commit message for each commit.
    """

    # Display the commit history
    display_commit_logs()


# Add the diff command
@cli.command()
@click.argument("blob1", required=True)
@click.argument("blob2", required=True)
@click.option("--path1", default=None, help="The path of the first file.")
@click.option("--path2", default=None, help="The path of the second file.")
@click.option(
    "--algorithm",
    default="myers",
    type=click.Choice(["myers", "unified"]),
    help="The diff algorithm to use.",
)
@click.option(
    "--context-lines",
    default=3,
    type=int,
    help="The number of context lines to show in the unified diff.",
)
def diff(
    blob1: str, blob2: str, path1: str, path2: str, algorithm: str, context_lines: int
):
    """Display the differences between two blob objects.

    Compare the contents of two blob objects and show the differences
    between them on a line-by-line basis.
    """

    # Get the repository path
    repo_path = pathlib.Path.cwd()

    # Print the diff
    print_diff(repo_path, blob1, blob2, path1, path2, algorithm, context_lines)


# Command to get all blob hashes from a commit
@cli.command()
@click.argument("commit", required=True)
def blobs(commit: str):
    """Display all blob hashes from a specified commit.

    This command retrieves and displays all blob hashes associated with files
    in the specified commit's tree. The commit can be specified using its hash,
    a branch name, or a tag.
    """

    # Get the repository path
    repo_path = pathlib.Path.cwd()

    try:
        # Validate the commit reference
        commit_hash = validate_commit_reference(repo_path, commit)
        if not commit_hash:
            # Log the error and exit
            logger.error(f"Invalid commit reference: {commit}")
            sys.exit(1)

        # Read the commit object
        object_type, content = read_git_object(repo_path, commit_hash)
        if object_type != "commit":
            # Log the error and exit
            logger.error(f"Object {commit_hash} is not a commit")
            sys.exit(1)

        # Parse the commit to get the tree hash
        commit_info = parse_commit_object(content)
        tree_hash = commit_info.get("tree")
        if not tree_hash:
            # Log the error and exit
            logger.error("No tree found in commit")
            sys.exit(1)

        # Create a table for displaying blob information
        table = Table(
            title=f"[bold blue]Blob Hashes in Commit {commit_hash[:8]}[/bold blue]",
            border_style="blue",
        )
        table.add_column("Blob Hash", style="cyan")
        table.add_column("File Path", style="green")

        # Function to recursively process tree objects
        def process_tree(tree_hash: str, prefix: str = ""):
            # Read the tree object
            object_type, content = read_git_object(repo_path, tree_hash)
            if object_type != "tree":
                return

            # Parse the tree entries
            entries = parse_tree_object(content)
            for entry in entries:
                mode, obj_type, obj_hash, name = entry

                # If it's a blob, add it to the table
                if obj_type == "blob":
                    table.add_row(obj_hash, f"{prefix}{name}")
                # If it's a tree, process it recursively
                elif obj_type == "tree":
                    process_tree(obj_hash, f"{prefix}{name}/")

        # Process the root tree
        process_tree(tree_hash)

        # Display the table
        console.print(table)

    except Exception as e:
        # Log the error and exit
        logger.error(f"Error retrieving blob hashes: {str(e)}")
        sys.exit(1)


# Branch command to create a new branch
@cli.command()
@click.argument("branch_name", required=False)
@click.option(
    "--commit",
    "-c",
    default=None,
    help="The commit hash to create the branch from. Defaults to HEAD.",
)
@click.option(
    "--delete",
    "-d",
    is_flag=True,
    help="Delete the specified branch.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force operation, such as deleting the current branch.",
)
@click.option(
    "--list",
    "-l",
    is_flag=True,
    help="List all branches in the repository.",
)
def branch(branch_name: str, commit: str, delete: bool, force: bool, list: bool):
    """Manage Git branches.

    This command can create, delete, or list branches. By default, it creates a branch
    pointing to the current HEAD or a specified commit.
    """

    try:
        # Get the current directory
        current_dir = pathlib.Path.cwd()

        if list:
            # List all branches
            # Get the current branch
            current = get_current_branch(current_dir)

            # Get all branches
            all_branches = list_branches(current_dir)

            # Create a table for the branches
            table = Table(title="[bold blue]Branches[/bold blue]", border_style="blue")
            table.add_column("Current", style="cyan", justify="center")
            table.add_column("Branch", style="green")

            # Check if there are any branches
            if not all_branches:
                logger.error("No branches found")
                return

            # Add the branches to the table
            for branch in all_branches:
                # Mark the current branch with an asterisk
                is_current = branch == current
                marker = "✓" if is_current else ""

                # Add the branch to the table
                table.add_row(
                    marker, f"[bold]{branch}[/bold]" if is_current else branch
                )

            # Print the table
            console.print(table)
        elif delete:
            # Delete the branch
            delete_branch(current_dir, branch_name, force)
        elif branch_name:
            # Create the branch
            create_branch(current_dir, branch_name, commit)
        else:
            # No operation specified and no branch name provided
            logger.error("Branch name is required unless --list is specified")

    except Exception as e:
        # Log the error
        logger.error(f"Error managing branch: {str(e)}")


# Checkout command to update the repository state
@cli.command()
@click.argument("target", required=True)
@click.argument("paths", nargs=-1, type=click.Path())
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force checkout even if there are uncommitted changes that would "
    "be overwritten.",
)
def checkout(target: str, paths: tuple, force: bool):
    """Checkout a branch, commit, or restore files.

    This command updates the repository state to match a target branch or commit,
    or restores specific files from a target branch or commit.
    """

    # Determine if we're doing a file restore or branch/commit checkout
    if paths:
        # We're restoring specific files
        paths_list = list(paths)

        # Display what we're doing
        if len(paths_list) == 1:
            logger.error(f"Restoring file '{paths_list[0]}' from {target}")
        else:
            logger.error(f"Restoring {len(paths_list)} files from {target}")

        # Restore the files
        if not restore_files(paths_list, target, force=force):
            logger.error("Failed to restore files.")
            sys.exit(1)
    else:
        # We're checking out a branch or commit
        logger.error(f"Checking out {target}")

        # Switch to the target branch or commit
        if not switch_branch_or_commit(target, force):
            logger.error("Checkout failed.")
            sys.exit(1)


# Merge command to perform a three-way merge with the current branch
@cli.command()
@click.argument("base", required=True)
@click.argument("other", required=True)
def merge(base: str, other: str):
    """Perform a three-way merge with the current branch.

    Merge changes from BRANCH or COMMIT into the current branch, with BASE
    as the common ancestor. Conflicts will be displayed in a tabular format
    for manual resolution.
    """

    try:
        # Validate the commits
        if not validate_commit_reference(base):
            # Log the error and exit
            logger.error(f"Invalid base commit: {base}")
            sys.exit(1)

        if not validate_commit_reference(other):
            # Log the error and exit
            logger.error(f"Invalid other commit: {other}")
            sys.exit(1)

        # Perform the merge
        conflicts = perform_merge(base, other)

        # Exit with a status code indicating if there were conflicts
        if conflicts > 0:
            # Log the warning
            logger.warning(
                f"Merge completed with {conflicts} conflict(s). "
                f"Manual resolution required."
            )

            # Exit with a status code of 1
            sys.exit(1)
        else:
            # Log the info
            logger.info("Merge completed successfully with no conflicts.")

            # Exit with a status code of 0
            sys.exit(0)

    except Exception as e:
        # Log the error and exit
        logger.error(f"Error performing merge: {str(e)}")
        sys.exit(1)
