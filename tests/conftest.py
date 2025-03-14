"""
Pytest configuration file.

This module contains configuration for pytest.
"""


# Function to configure pytest
def pytest_configure(config):
    """
    Configure pytest for the Clony project.

    Args:
        config: The pytest configuration object.
    """

    # Add custom markers
    config.addinivalue_line("markers", "cli: mark test as a CLI test")
    config.addinivalue_line("markers", "unit: mark test as a unit test")
