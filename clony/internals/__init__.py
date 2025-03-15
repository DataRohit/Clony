"""
Internals module for Clony.

This module contains internal utilities and helpers for the Clony Git clone tool.
"""

# Local imports
from clony.internals.commit import make_commit
from clony.internals.staging import stage_file

# Export the internals
__all__ = ["make_commit", "stage_file"]
