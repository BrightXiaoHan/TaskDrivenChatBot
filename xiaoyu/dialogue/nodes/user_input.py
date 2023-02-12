"""
用户输入节点
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict

from xiaoyu.dialogue.nodes.base import BaseNode, ForwardIterator, callback_cycle_checker

if TYPE_CHECKING:
    from xiaoyu.dialogue.context import StateTracker

__all__ = ["UserInputNode"]


class UserInputNode(BaseNode):
    NODE_NAME = "用户输入节点"

    optional_checkers: Dict[str, Callable] = dict(life_cycle=callback_cycle_checker(), callback_words=callback_cycle_checker())

    traceback_template: Dict[str, Any] = {"type": "userSay", "node_name": ""}

    def call(self, context: StateTracker) -> ForwardIterator:
        return ForwardIterator(self, context, life_cycle=self.config.get("life_cycle", 0))
