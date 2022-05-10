"""Global fixtures for pytest."""
import pytest
from utils.funcs import generate_uint


@pytest.fixture(scope="session")
def robot_code():
    """Robot code for all test cases."""
    return generate_uint()
