"""
回复节点
"""
from backend.dialogue.nodes.base import _BaseNode

__all__ = ["ReplyNode"]


class ReplyNode(_BaseNode):
    NODE_NAME = '回复节点'

    def __call__(self, context):
        yield context.decode_ask_words(self.config["content"])
        msg = context._latest_msg()

        if msg.intent in self.intent_child:
            yield self.intent_child[msg.intent]
        else:
            yield self.default_child
