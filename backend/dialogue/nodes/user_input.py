"""
用户输入节点
"""
from backend.dialogue.nodes.base import _TriggerNode, _MultiBranchNode


class UserInputNode(_TriggerNode, _MultiBranchNode):
    def __call__(self, context):
        branch_id = self.choose(context)
        yield self.get_child(branch_id)

    def trigger(self, msg):
        if msg.intent in self.config["intent_id"]:
            return msg.intent_confidence
        else:
            return 0
