"""
机器人说节点
"""
from __future__ import annotations

import random
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Dict, List

from xiaoyu.dialogue.nodes.base import (
    BaseIterator,
    BaseNode,
    ForwardIterator,
    OptionIterator,
    callback_cycle_checker,
    simple_type_checker,
)
from xiaoyu.dialogue.nodes.judge import JudgeNode
from xiaoyu.utils.exceptions import (
    DialogueRuntimeException,
    DialogueStaticCheckException,
)

if TYPE_CHECKING:
    from xiaoyu.dialogue.context import StateTracker

__all__ = ["RobotSayNode"]


class RobotSayNodeIterator(BaseIterator):
    async def run_state_0(self) -> str:
        # 如果回复节点包含选项，则将选项添加到当前message里面
        options = self.node.config.get("options", [])
        msg = self.context.latest_msg()
        msg.options = options

        if "branchs" in self.node.config:
            # 否则进入条件判断，根据不通条件生成不通的回复话术
            for branch in self.node.config["branchs"]:
                if "conditions" not in branch:
                    continue
                conditions = branch["conditions"]
                if self.node._judge_branch(self.context, conditions):
                    self.state = 1
                    return random.choice(branch["content"])

        if "content" in self.node.config:
            # 如果配置的回复话术为固定的一个字符串
            self.state = 1
            return random.choice(self.node.config["content"])
        else:
            raise DialogueRuntimeException("没有触发条件回复，同时也没有配置固定回复内容", self.context.robot_code, self.node.config["node_name"])

    async def run_satet_1(self) -> str:
        self.end()
        life_cycle = self.node.config.get("life_cycle", 0)
        if bool(self.node.option_child):
            self.child = OptionIterator(self.node, self.context, repeat_times=life_cycle)
        else:
            self.child = ForwardIterator(self.node, self.context, life_cycle=life_cycle)


class RobotSayNode(BaseNode):
    NODE_NAME = "机器人说节点"

    @staticmethod
    def say_node_conditional_checker(node: BaseNode, branchs: List[Dict[str, Any]]) -> None:
        if not isinstance(branchs, list):
            reason = "branchs字段的类型必须是list，而现在是{}".format(type(branchs))
            raise DialogueStaticCheckException("branchs", reason=reason, node_id=node.node_name)

        for branch in branchs:
            if not isinstance(branch, dict):
                reason = "branchs字段中每个branch的类型必须是dict，目前是{}".format(type(branch))
                raise DialogueStaticCheckException("branchs", reason, node_id=node.node_name)

            if "conditions" not in branch or not isinstance(branch["conditions"], list):
                reason = "branchs字段中的每个group必须有conditions字段，并且是list类型"
                raise DialogueStaticCheckException("branchs", reason, node_id=node.node_name)

            if "content" not in branch or not isinstance(branch["content"], list):
                reason = "branchs字段中的每个group必须有content字段，并且是list类型"
                raise DialogueStaticCheckException("branchs", reason, node_id=node.node_name)

            for condition in branch["conditions"]:
                if not isinstance(condition, list):
                    reason = "branchs字段中每个group的conditions字段必须是list，而现在是{}".format(type(condition))
                    raise DialogueStaticCheckException("slots", reason=reason, node_id=node.node_name)

                for group in condition:
                    JudgeNode._check_condition(node, group)

    optional_checkers: Dict[str, Callable] = dict(
        life_cycle=callback_cycle_checker(),
        callback_words=callback_cycle_checker(),
        branchs=say_node_conditional_checker,
        content=simple_type_checker("content", list),
        strict=simple_type_checker("strict", bool),
    )

    traceback_template: Dict[str, Any] = {"type": "robotSay", "node_name": "", "is_end": False}

    def static_check(self) -> None:
        super().static_check()
        if "branchs" not in self.config and "content" not in self.config:
            raise DialogueStaticCheckException(
                "content, branchs",
                "机器人说节点必须配置branchs或者content字段",
                node_id=self.node_name,
            )

    def call(self, context: StateTracker) -> BaseIterator:
        # TODO 这里目前暂时这么判断，回复节点如果没有子节点则判断本轮对话结束
        if not self.default_child and not self.intent_child and not self.option_child:
            context.is_end = True
            context.dialog_status = "20"  # 此处为机器人挂断的状态码
            # 记录调试信息
            context.update_traceback_data("is_end", True)

        return RobotSayNodeIterator(self, context)
