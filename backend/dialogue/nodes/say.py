"""
机器人说节点
"""
from backend.dialogue.nodes.user_input import UserInputNode

__all__ = ["SayNode"]


class SayNode(UserInputNode):
    NODE_NAME = "机器人说节点"

    def __call__(self, context):
        # 如果机器人说节点包含选项，则将选项添加到当前message里面
        options = self.config.get("options", [])
        msg = context._latest_msg()
        msg.options = options

        yield self.config["ask_words"]
        yield from super(SayNode, self).__call__(context)
