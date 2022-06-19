import pytest

from backend.dialogue.agent import Agent
from backend.dialogue.context import StateTracker
from backend.nlu.interpreter import Message


@pytest.fixture(scope="function")
def context(robot_code):
    agent = Agent(robot_code, None, {})
    context = StateTracker(agent, user_id="test_user", params={})
    return context


@pytest.fixture(scope="function")
def msg(context):
    """模拟消息"""
    raw_msg = {"text": "", "intent": "", "entities": {}}
    msg = Message(raw_msg, context.robot_code)

    # 加入一个空消息
    context.msg_recorder.append(msg)
    return msg
