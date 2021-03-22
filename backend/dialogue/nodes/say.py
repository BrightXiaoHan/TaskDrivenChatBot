"""
机器人说节点
"""
from backend.dialogue.nodes.base import _TriggerNode


class SayNode(_TriggerNode):

    def _trigger(self):
        # 该节点一定会被触发
        return 1

    def __call__(self, msg):
        msg = yield self.config["ask_words"]

        # 需要填充的全局槽位
        slots = self.config["global_slots"]
        # 获取未被填充的槽位
        slots = [slot for slot in slots
                 if self.context.slots[slot] is None]

        abilities = msg.get_abilities()

        for slot in slots:
            if slot in abilities:
                self.context.fill_slot(slot, abilities[slot][0])

        slots = [slot for slot in slots
                 if self.context.slots[slot] is None]

        yield self.get_child()
