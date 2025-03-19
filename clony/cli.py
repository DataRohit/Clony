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
from clony.core.diff import print_diff
from clony.core.repository import Repository
from clony.internals.commit import make_commit
from clony.internals.log import display_commit_logs
from clony.internals.reset import reset_head
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
    Clony: A modern Git clone tool with a cool CLI interface.

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
        # Print the error
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

        # Exit the program
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
    provided, initializes in the current directory."""

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

    The file path is required, while the file must exist before proceeding.
    """

    # Check if file exists before proceeding
    if not pathlib.Path(path).exists():
        logger.error(f"File not found: '{path}'")
        return

    # Stage the file using the staging module
    stage_file(path)


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

    The commit message is required, while author name and email are optional
    and will default to "Clony User" and "user@example.com" if not provided.
    """

    # Set default author name and email if not provided
    if not author_name:
        author_name = "Clony User"
    if not author_email:
        author_email = "user@example.com"

    # Create the commit using the commit module
    make_commit(message, author_name, author_email)


# Status command to show the working tree status
@cli.command()
@click.argument("path", type=click.Path(), default=".")
def status(path: str):
    """Show the working tree status.

    This command displays the state of the working directory and the staging area.
    It shows which changes have been staged, which haven't, and which files aren't
    being tracked by Git.
    """

    try:
        # Get the status of the repository
        _, formatted_status = get_status(path)

        # Display the status with styling
        print("\nOn branch main\n")
        print(formatted_status)

    except Exception as e:
        # Log the error and display an error message
        logger.error(f"Error showing status: {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
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

    # Determine the reset mode
    if soft:
        mode = "soft"
    elif hard:
        mode = "hard"
    else:
        # Default to mixed mode
        mode = "mixed"

    # Perform the reset
    success = reset_head(commit, mode)

    # Handle failure
    if not success:
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
    between them on a line-by-line basis."""

    # Get the repository path
    repo_path = pathlib.Path.cwd()

    # Print the diff
    print_diff(repo_path, blob1, blob2, path1, path2, algorithm, context_lines)
