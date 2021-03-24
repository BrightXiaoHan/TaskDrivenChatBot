"""
填槽节点
"""
import random

from backend.dialogue.nodes.base import _BaseNode


class FillSlotsNode(_BaseNode):

    def __call__(self, msg):
        slots = self.config["slots"]
        for slot in slots:
            repeat_times = 0
            if msg.intent in self.intent_child:
                yield self.intent_child[msg.intent]
            else:
                abilities = msg.get_abilities()
                if slot["slot_name"] in abilities:
                    self.context.fill_slot(slot, abilities[slot][0])
                else:
                    repeat_times += 1
                    if repeat_times > slot["rounds"]:
                        self.context.fill_slot(slot, "unkown")
                    else:
                        yield random.choice(slot["reask_words"])

        yield self.default_child
