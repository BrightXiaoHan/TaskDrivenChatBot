"""
回复节点
"""
from backend.dialogue.nodes.base import _BaseNode

__all__ = ["ReplyNode"]


class ReplyNode(_BaseNode):
    __name__ = '回复节点'

    def __call__(self, context):
        yield context.decode_ask_words(self.config["content"])
