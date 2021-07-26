"""
机器人说节点
"""
from backend.dialogue.nodes.user_input import UserInputNode

__all__ = ["SayNode"]


class SayNode(UserInputNode):
    NODE_NAME = "机器人说节点"

    def __call__(self, context):
        yield self.config["ask_words"]
        if bool(self.option_child):
            yield from self.options(context)
        else:
            yield from super(SayNode, self).__call__(context)
