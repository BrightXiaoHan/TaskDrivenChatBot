"""
填槽节点
"""
import random

from backend.dialogue.nodes.base import _BaseNode
from backend.dialogue.nodes.builtin import builtin_entities
from backend.dialogue.nodes.builtin.hard_code import hard_code_entities
from utils.exceptions import DialogueStaticCheckException

__all__ = ["FillSlotsNode"]


def fill_slot_node_slots_checker(node, slots):
    if not isinstance(slots, list):
        reason = "填槽节点的slots字段必须是list类型，现在是{}类型".format(type(slots))
        raise DialogueStaticCheckException("slots", reason, node.node_name)

    for slot in slots:
        if "slot_name" not in slot or not isinstance(slot["slot_name"], str):
            reason = "填槽节点的slots字段中每个元素必须有slot_name字段，并且必须是str类型"
            raise DialogueStaticCheckException("slots", reason, node.node_name)

        if "multi" not in slot or not isinstance(slot["multi"], bool):
            reason = "填槽节点的slots字段中每个元素必须有multi字段，并且必须是bool类型"
            raise DialogueStaticCheckException("slots", reason, node.node_name)

        if "rounds" not in slot or not isinstance(slot["rounds"], int):
            reason = "填槽节点的slots字段每个元素必须有rounds字段，并且必须是int类型"
            raise DialogueStaticCheckException("slots", reason, node.node_name)

        if "reask_words" not in slot or not isinstance(slot["reask_words"], list):
            reason = "填槽节点的slots字段中每个元素必须有reask_words字段，并且必须是list类型"
            raise DialogueStaticCheckException("slots", reason, node.node_name)
        if "callback_words" not in slot or not isinstance(slot["callback_words"], list):
            reason = "填槽节点的slots字段中每个元素必须有callback_words字段，并且必须是list类型"
            raise DialogueStaticCheckException("slots", reason, node.node_name)

        if "is_necessary" not in slot or not isinstance(slot["is_necessary"], bool):
            reason = "填槽节点的slots字段中每个元素必须有is_necessary字段，并且必须是bool类型"
            raise DialogueStaticCheckException("slots", reason, node.node_name)


class FillSlotsNode(_BaseNode):

    NODE_NAME = "填槽节点"

    required_checkers = dict(
        slots=fill_slot_node_slots_checker
    )

    traceback_template = {
        "type": "fillSlot",
        "node_name": "",
        "info": []
    }

    async def call(self, context):
        slots = self.config["slots"]
        num_slots = len(slots)
        cur = 0
        repeat_times = 0
        while cur < num_slots:

            slot = slots[cur]
            slot_name = slot["slot_name"]
            # 兼容处理，如果老版本配置没有这个字段也可以运行
            slot_alias = slot.get("slot_alias", slot_name)
            ability = context.get_ability_by_slot(slot_name)
            msg = context._latest_msg()

            # 内置节点识别
            if ability in builtin_entities:
                for item in builtin_entities[ability](msg):
                    yield item

            # hard coding 识别
            if ability in hard_code_entities:
                for item in hard_code_entities[ability](msg):
                    yield item

            # 意图强制跳转，放在内置实体识别之后，为了保证@recent_intent可以识别
            # forward操作中可能会覆盖原始的intent
            async for item in  self.forward(context, use_default=False):
                yield item

            abilities = msg.get_abilities()
            warning = slot.get("warning", False)
            prefix = slot.get("prefix_context", "")
            suffix = slot.get("suffix_context", "")
            if ability in abilities:
                context.fill_slot(slot_name, abilities[ability][0], slot_alias, warning, prefix, suffix)
                # 添加调试信息
                context.update_traceback_data("info", {
                    "name": slot_name,
                    "value": abilities[ability][0],
                    "ability": ability
                })
                cur += 1
                repeat_times = 0
            else:
                if repeat_times >= slot["rounds"] and not slot.get(
                        "is_necessary", False):
                    context.fill_slot(slot_name, "unkown", slot_alias, warning, prefix, suffix)
                    context.update_traceback_data("info", {
                        "name": slot_name,
                        "value": "unkown",
                        "ability": "超过询问次数自动填充为unkown"
                    })
                    cur += 1
                    repeat_times = 0
                else:
                    msg.understanding = "2"
                    yield random.choice(slot["reask_words"])
                repeat_times += 1

        if self.default_child:
            context.add_traceback_data({
                "type": "conn",
                "line_id": self.line_id_mapping[self.default_child.node_name],
                "conn_type": "default",
                "source_node_name": self.node_name,
                "target_node_name": self.default_child.node_name
            })
        yield self.default_child
