"""
填槽节点
"""
import random

from backend.dialogue.nodes.base import _BaseNode

__all__ = ["FillSlotsNode"]


class FillSlotsNode(_BaseNode):

    NODE_NAME = "填槽节点"

    def __call__(self, context):
        slots = self.config["slots"]
        num_slots = len(slots)
        cur = 0
        while cur < num_slots:
            slot = slots[cur]
            repeat_times = 0
            msg = context._latest_msg()

            if msg.intent in self.intent_child:
                yield self.intent_child[msg.intent]
            else:
                abilities = msg.get_abilities()
                slot_name = slot["slot_name"]
                ability = context.get_ability_by_slot(slot_name)
                if ability in abilities:
                    context.fill_slot(slot_name, abilities[ability][0])
                    cur += 1
                else:
                    if repeat_times > slot["rounds"]:
                        context.fill_slot(slot_name, "unkown")
                        cur += 1
                    else:
                        yield random.choice(slot["reask_words"])
                    repeat_times += 1

        yield self.default_child
