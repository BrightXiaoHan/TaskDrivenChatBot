"""
填槽节点
"""
from __future__ import annotations

import random
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from xiaoyu.dialogue.nodes.base import BaseIterator, BaseNode, ForwardIterator
from xiaoyu.nlu.builtin import builtin_ne_extract
from xiaoyu.utils.exceptions import DialogueStaticCheckException

if TYPE_CHECKING:
    from xiaoyu.dialogue.context import StateTracker

__all__ = ["FillSlotsNode"]


class FillSlotsNodeIterator(BaseIterator):
    def __init__(self, node: BaseNode, context: StateTracker):
        super().__init__(node, context)
        self.num_slots = len(node.config["slots"])
        self.cur = 0
        self.repeat_times = 0
        self.slots = node.config["slots"]

    async def run_state_1(self) -> Optional[str]:
        msg = self.context.latest_msg()
        slot = self.slots[self.cur]
        abilities = msg.get_abilities()
        warning = slot.get("warning", False)
        slot_name = slot["slot_name"]
        slot_alias = slot.get("slot_alias", slot_name)
        ability = self.context.get_ability_by_slot(slot_name)

        if ability in abilities:
            self.context.fill_slot(slot_name, abilities[ability][0], slot_alias, warning)
            # 添加调试信息
            self.context.update_traceback_data("info", {"name": slot_name, "value": abilities[ability][0], "ability": ability})
            self.cur += 1
            self.repeat_times = 0
        else:
            if self.repeat_times >= slot["rounds"] and not slot.get("is_necessary", False):
                self.context.fill_slot(slot_name, "unkown", slot_alias, warning)
                self.context.update_traceback_data(
                    "info", {"name": slot_name, "value": "unkown", "ability": "超过询问次数自动填充为unkown"}
                )
                self.cur += 1
                self.repeat_times = 0
            else:
                msg.understanding = "2"
                self.state = 0
                self.repeat_times += 1
                return random.choice(slot["reask_words"])

        return await self.run_state_0()

    async def run_state_0(self) -> Optional[str]:
        if self.cur < self.num_slots:
            slot = self.slots[self.cur]
            slot_name = slot["slot_name"]
            # 兼容处理，如果老版本配置没有这个字段也可以运行
            ability = self.context.get_ability_by_slot(slot_name)
            msg = self.context.latest_msg()

            # 内置节点识别
            builtin_ne_extract(msg, ability)

            # 意图强制跳转，放在内置实体识别之后，为了保证@recent_intent可以识别
            # forward操作中可能会覆盖原始的intent

            self.child = ForwardIterator(self.context, self.node, use_default=False)
            self.state = 1
            return

        if self.default_child:
            self.context.add_traceback_data(
                {
                    "type": "conn",
                    "line_id": self.line_id_mapping[self.default_child.node_name],
                    "conn_type": "default",
                    "source_node_name": self.node_name,
                    "target_node_name": self.default_child.node_name,
                }
            )

        self.next_node = self.node.default_child
        return self.end()


class FillSlotsNode(BaseNode):
    NODE_NAME = "填槽节点"

    @staticmethod
    def fill_slot_node_slots_checker(node: FillSlotsNode, slots: List[Dict[str, Any]]) -> None:
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

    required_checkers: Dict[str, Callable] = dict(slots=fill_slot_node_slots_checker)

    traceback_template: Dict[str, Any] = {"type": "fillSlot", "node_name": "", "info": []}

    def call(self, context: StateTracker) -> FillSlotsNodeIterator:
        return FillSlotsNodeIterator(self, context)
