"""Global fixtures for pytest."""
import pytest


@pytest.fixture(scope="session")
def robot_code():
    """Return the robot code."""
    return "pytest_robot_code"
