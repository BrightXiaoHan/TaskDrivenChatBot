import os

from backend.nlu import get_interpreter
from backend.dialogue.context import StateTracker


class Agent(object):
    """
    会话管理类

    Attributes:
        robot_
        interpreter (backend.nlu.interpreter.CustormInterpreter): nlu语义理解器
        user_store (dict): 会话状态存储字典。key为会话id，value为 `StateTracker`对象
    """

    def __init__(
        self,
        robot_code
    ):
        self.robot_code = robot_code
        self.interpreter = get_interpreter(robot_code)
        # save the user states in memory
        self.user_store = dict()

    def handle_message(
        self,
        message,
        sender_id
    ):
        """回复用户

        Args:
            message (str): 用户说话的内容
            sender_id (str): 会话id

        Returns:
            dict: 小语会话信息
        """
        state_tracker = self._get_user_state_tracker(sender_id)
        raw_message = self.interpreter.parse(message)
        state_tracker.handle_message(raw_message)
        return self.user_store.get(sender_id).get_latest_xiaoyu_pack()

    def _get_user_state_tracker(self, sender_id):
        if sender_id not in self.user_store:
            tracker = StateTracker(sender_id)
            self.user_store.update({sender_id: tracker})

        return self.user_store.get(sender_id)

    def get_logger(self, uid):
        if uid not in self.user_store:
            return None
        return self.user_store.get(uid).get_logger()

    def hang_up(self, uid):
        if uid not in self.user_store:
            return
        self.user_store.get(uid).hang_up()

    def get_xiaoyu_pack(self, uid):
        if uid not in self.user_store:
            return None
        return self.user_store.get(uid).get_xiaoyu_pack()

    def get_latest_xiaoyu_pack(self, uid):

        if uid not in self.user_store:
            return None
        return self.user_store.get(uid).get_latest_xiaoyu_pack()
