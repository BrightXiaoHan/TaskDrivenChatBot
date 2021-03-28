"""
机器人说节点
"""
from backend.dialogue.nodes.user_input import UserInputNode

__all__ = ["SayNode"]


class SayNode(UserInputNode):
    NODE_NAME = "机器人说节点"

    def __call__(self, context):
        yield context.decode_ask_words(self.config["ask_words"])
        yield from super(SayNode, self).__call__(context)

    def trigger(self, context):
        return True
