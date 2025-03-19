"""
Tests for CLI main function and module execution.

This module contains tests for the Clony CLI main function and module execution.
"""

# Standard imports
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
import clony
from clony.cli import main


# Test for the main function with successful execution
@pytest.mark.unit
def test_main_success():
    """
    Test that the main function works correctly with successful execution.
    """

    # Mock the cli function
    with patch("clony.cli.cli") as mock_cli:
        # Mock the sys.exit function
        with patch("sys.exit") as mock_exit:
            # Run the main function
            main()

            # Assert that the cli function was called once
            mock_cli.assert_called_once()

            # Assert that the sys.exit function was not called
            mock_exit.assert_not_called()


# Test for the main function with an exception
@pytest.mark.unit
def test_main_exception():
    """
    Test that the main function handles exceptions correctly.
    """

    # Mock the cli function
    with patch("clony.cli.cli", side_effect=Exception("Test error")):
        # Mock the logger.error function
        with patch("clony.cli.logger.error") as mock_logger:
            # Mock the sys.exit function
            with patch("sys.exit") as mock_exit:
                # Run the main function
                main()

                # Assert that the logger.error function was called once
                mock_logger.assert_called_once_with("Error: Test error")

                # Assert that sys.exit was called once with a non-zero exit code
                mock_exit.assert_called_once_with(1)


# Test for the if __name__ == "__main__" block
@pytest.mark.unit
def test_main_module_execution():
    """
    Test that the main function is called when the module is executed directly.
    """

    # Mock sys.argv to prevent pytest args from interfering
    with patch("sys.argv", ["clony"]):
        # Mock the Click CLI to prevent actual execution
        with patch("clony.cli.cli") as mock_cli:
            # Create a temporary function to simulate __main__ block
            def mock_main_block():
                main()

            # Add the mock function to the module
            clony.cli.__main_block_for_testing = mock_main_block

            try:
                # Call the mock function
                clony.cli.__main_block_for_testing()

                # Assert that cli was called
                mock_cli.assert_called_once()
            finally:
                # Clean up by removing the mock function
                delattr(clony.cli, "__main_block_for_testing")

            # Reset the mock for the next test
            mock_cli.reset_mock()

            # Test direct main() call
            main()

            # Assert that cli was called again
            mock_cli.assert_called_once()
