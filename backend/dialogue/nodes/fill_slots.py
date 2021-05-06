"""
填槽节点
"""
import random

from backend.dialogue.nodes.base import _BaseNode
from backend.dialogue.nodes.builtin import builtin_nodes

__all__ = ["FillSlotsNode"]


class FillSlotsNode(_BaseNode):

    NODE_NAME = "填槽节点"

    def __call__(self, context):
        slots = self.config["slots"]
        num_slots = len(slots)
        cur = 0
        repeat_times = 0
        while cur < num_slots:
            # 意图强制跳转
            yield from self.forward(context, use_default=False)

            slot = slots[cur]
            slot_name = slot["slot_name"]
            ability = context.get_ability_by_slot(slot_name)
            msg = context._latest_msg()

            # 内置节点识别
            if ability in builtin_nodes:
                yield from builtin_nodes[ability](context, slot_name)
                if slot.get("is_nessesary", False) and context.slots[slot_name] is None:
                    context.fill_slot(slot_name, "unkown")
                    cur += 1
                elif context.slots[slot_name] is None:
                    yield random.choice(slot["reask_words"])
                else:
                    cur += 1
            else:
                abilities = msg.get_abilities()
                if ability in abilities:
                    context.fill_slot(slot_name, abilities[ability][0])
                    cur += 1
                    repeat_times = 0
                else:
                    if repeat_times >= slot["rounds"] and not slot.get(
                            "is_nessesary", False):
                        context.fill_slot(slot_name, "unkown")
                        cur += 1
                        repeat_times = 0
                    else:
                        if msg.understanding and len(
                                msg.faq_result["title"]
                        ) < len(msg.text) * 2 and len(
                                msg.faq_result["title"]) % 2 > len(msg.text):
                            yield msg.get_faq_answer() + "\n" + random.choice(
                                slot["callback_words"])
                        else:
                            yield random.choice(slot["reask_words"])
                    repeat_times += 1

        yield self.default_child
