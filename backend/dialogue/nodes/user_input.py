"""
用户输入节点
"""
from backend.dialogue.nodes.base import _TriggerNode

__all__ = ["UserInputNode"]


class UserInputNode(_TriggerNode):
    NODE_NAME = "用户输入节点"

    def __call__(self, context):
        msg = context._latest_msg()
        if msg.intent in self.intent_child:
            yield self.intent_child[msg.intent]
        else:
            yield self.default_child

    def trigger(self, context):
        conditions = self.config["condition_group"]
        return self._judge_branch(context, conditions)
