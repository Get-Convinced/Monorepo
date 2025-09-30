"""
Local conftest for unit tests - simpler setup without global fixtures.
"""

import pytest


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Override the global autouse fixture for unit tests.
    
    Unit tests should be isolated and not need auth/redis mocking.
    """
    # Just yield without doing anything
    yield
