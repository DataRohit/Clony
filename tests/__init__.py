"""
Test suite for Clony.

This package contains tests for the Clony Git clone tool.
The tests are organized into modules that mirror the structure of the main package:
- core: Tests for core functionality
- internals: Tests for internal utilities
- utils: Tests for utility functions
- test_cli_*.py: Tests for the command-line interface
"""

# Version information
__version__ = "0.1.0"

# Define the public API
__all__ = [
    "core",
    "internals",
    "test_cli_basic",
    "test_cli_display",
    "test_cli_init",
    "test_cli_main",
    "test_cli_stage",
    "utils",
]

# Import test modules
from tests import (
    core,
    internals,
    test_cli_basic,
    test_cli_display,
    test_cli_init,
    test_cli_main,
    test_cli_stage,
    utils,
)
