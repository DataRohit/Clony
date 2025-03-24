"""
Internals module for Clony.

This module contains internal utilities and helpers for the Clony Git clone tool.
"""

# Local imports
from clony.internals.checkout import restore_files, switch_branch_or_commit
from clony.internals.commit import make_commit
from clony.internals.log import display_commit_logs, get_commit_logs
from clony.internals.merge import perform_merge
from clony.internals.reset import reset_head
from clony.internals.staging import stage_file
from clony.internals.status import FileStatus, get_status

# Export the internals
__all__ = [
    "make_commit",
    "stage_file",
    "get_status",
    "FileStatus",
    "reset_head",
    "get_commit_logs",
    "display_commit_logs",
    "switch_branch_or_commit",
    "restore_files",
    "perform_merge",
]
