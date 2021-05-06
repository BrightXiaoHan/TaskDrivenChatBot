"""
回复节点
"""
from backend.dialogue.nodes.base import _BaseNode

__all__ = ["ReplyNode"]


class ReplyNode(_BaseNode):
    NODE_NAME = '回复节点'

    def __call__(self, context):
        yield self.config["content"]
        yield from self.forward(context)
