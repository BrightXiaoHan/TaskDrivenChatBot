"""
用户输入节点
"""
from backend.dialogue.nodes.base import _TriggerNode

__all__ = ["UserInputNode"]


class UserInputNode(_TriggerNode):
    NODE_NAME = "用户输入节点"

    def __call__(self, context):
        yield from self.forward(context)

    def trigger(self, context):
        conditions = self.config["condition_group"]
        return self._judge_branch(context, conditions)
