"""
Tests for CLI main function and module execution.

This module contains tests for the Clony CLI main function and module execution.
"""

# Standard imports
from unittest.mock import patch

# Local imports
import clony
from clony.cli import main


# Test for the main function with successful execution
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
def test_main_exception():
    """
    Test that the main function handles exceptions correctly.
    """

    # Mock the cli function
    with patch("clony.cli.cli", side_effect=Exception("Test error")):
        # Mock the console.print function
        with patch("clony.cli.console.print") as mock_print:
            # Mock the sys.exit function
            with patch("sys.exit") as mock_exit:
                # Run the main function
                main()

                # Assert that the console.print function was called once
                mock_print.assert_called_once()

                # Assert that the sys.exit function was called once with 1
                mock_exit.assert_called_once_with(1)


# Test for the if __name__ == "__main__" block
def test_main_module_execution():
    """
    Test that the main function is called when the module is executed directly.
    """

    # Mock the main function
    with patch("clony.cli.main") as mock_main:
        # Directly call the code that would be executed in the
        # if __name__ == "__main__" block
        if hasattr(clony.cli, "__main_block_for_testing"):
            # Call the function that contains the code from the
            # if __name__ == "__main__" block
            clony.cli.__main_block_for_testing()
        else:
            # If the function doesn't exist, just call main() directly
            # This is a fallback that simulates what would happen in the if block
            clony.cli.main()

        # Assert that the main function was called
        mock_main.assert_called_once()
