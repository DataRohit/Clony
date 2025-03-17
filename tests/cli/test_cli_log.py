"""
Tests for the log CLI command.

This module contains tests for the log CLI command.
"""

# Standard library imports
from unittest.mock import patch

# Third-party imports
import pytest
from click.testing import CliRunner

# Local imports
from clony.cli import cli


# Test for the log command
@pytest.mark.cli
def test_log_command():
    """
    Test the log command.
    """

    # Create a CLI runner
    runner = CliRunner()

    # Mock the display_commit_logs function
    with patch("clony.cli.display_commit_logs") as mock_display_logs:
        # Run the log command
        result = runner.invoke(cli, ["log"])

        # Assert that the command was successful
        assert result.exit_code == 0

        # Assert that the display_commit_logs function was called
        mock_display_logs.assert_called_once()
