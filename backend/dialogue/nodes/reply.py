"""
回复节点
"""
from backend.dialogue.nodes.base import _BaseNode


class ReplyNode(_BaseNode):
    def __call__(self, context):
        yield context.decode_ask_words(self.config["content"])
