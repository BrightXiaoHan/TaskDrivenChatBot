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
            # 需要填充的全局槽位
            slots = self.config["global_slots"]
            # 获取未被填充的槽位
            slots = [slot for slot in slots
                     if context.slots[slot] is None]

            slots = {slot: context.slots_abilities[slot] for slot in slots}

            abilities = msg.get_abilities()

            for slot, ability in slots.items():
                if ability in abilities:
                    context.fill_slot(slot, abilities[ability][0])

            yield self.default_child

    def trigger(self, context):
        conditions = self.config["condition_group"]
        return self._judge_branch(conditions)
