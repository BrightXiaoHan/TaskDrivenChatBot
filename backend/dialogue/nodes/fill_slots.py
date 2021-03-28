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
        for slot in slots:
            repeat_times = 0
            msg = context._latest_msg()

            if msg.intent in self.intent_child:
                yield self.intent_child[msg.intent]
            else:
                abilities = msg.get_abilities()
                slot_name = slot["slot_name"]
                ability = context.slots_abilities[slot_name]
                if ability in abilities:
                    context.fill_slot(slot_name, abilities[ability][0])
                else:
                    repeat_times += 1
                    if repeat_times > slot["rounds"]:
                        context.fill_slot(slot_name, "unkown")
                    else:
                        yield random.choice(slot["reask_words"])

        yield self.default_child
