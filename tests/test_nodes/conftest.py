import pytest

from backend.dialogue.agent import Agent
from backend.dialogue.context import StateTracker


@pytest.fixture(scope="function")
def context(robot_code):
    agent = Agent(robot_code, None, {})
    context = StateTracker(agent, user_id="test_user")
    pass
