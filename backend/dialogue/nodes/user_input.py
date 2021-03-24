"""
用户输入节点
"""
from backend.dialogue.nodes.base import _TriggerNode


class UserInputNode(_TriggerNode):
    def __call__(self, context):
        msg = context._latest_msg()
        if msg.intent in self.intent_child:
            yield self.intent_child[msg.intent]
        else:
            # 需要填充的全局槽位
            slots = self.config["global_slots"]
            # 获取未被填充的槽位
            slots = [slot for slot in slots
                     if self.context.slots[slot] is None]

            abilities = msg.get_abilities()

            for slot in slots:
                if slot in abilities:
                    self.context.fill_slot(slot, abilities[slot][0])

            yield self.get_child()

    def trigger(self, context):
        pass
