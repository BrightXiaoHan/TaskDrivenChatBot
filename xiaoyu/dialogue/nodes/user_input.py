"""
用户输入节点
"""
from backend.dialogue.nodes.base import _BaseNode, callback_cycle_checker

__all__ = ["UserInputNode"]


class UserInputNode(_BaseNode):
    NODE_NAME = "用户输入节点"

    optional_checkers = dict(
        life_cycle=callback_cycle_checker(), callback_words=callback_cycle_checker()
    )

    traceback_template = {"type": "userSay", "node_name": ""}

    async def call(self, context):
        async for item in self.forward(
            context, life_cycle=self.config.get("life_cycle", 0)
        ):
            return item
