"""
Clony - A modern Git clone tool with a cool CLI interface.

This package provides a Python-based Git clone tool with a modern CLI interface.
"""

# Version information
try:
    from clony._version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = "0.1.12"  # Fallback version

# Import core modules for easier access
from clony.core.repository import Repository
from clony.internals.staging import stage_file
from clony.utils.logger import logger

# Make these modules available at the package level
__all__ = [
    "Repository",
    "stage_file",
    "logger",
    "__version__",
]
