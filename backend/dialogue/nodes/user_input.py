"""
用户输入节点
"""
from backend.dialogue.nodes.base import _BaseNode

__all__ = ["UserInputNode"]


class UserInputNode(_BaseNode):
    NODE_NAME = "用户输入节点"

    def __call__(self, context):
        yield from self.forward(context)
