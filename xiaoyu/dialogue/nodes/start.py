"""
开始节点
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List

from xiaoyu.dialogue.nodes.base import TriggerNode
from xiaoyu.utils.exceptions import DialogueStaticCheckException

if TYPE_CHECKING:
    from xiaoyu.dialogue.context import StateTracker
    from xiaoyu.dialogue.nodes.base import ForwardIterator

__all__ = ["StartNode"]


class StartNode(TriggerNode):
    NODE_NAME = "开始节点"

    @staticmethod
    def _check_condition(node: StartNode, condition: Dict[str, Any]) -> bool:
        if "type" not in condition:
            reason = "condition_group字段中每个判断条件必须有type字段"
            raise DialogueStaticCheckException("condition_group", reason, node.node_name)

        if "operator" not in condition:
            reason = "condition_group字段中每个判断条件必须有operator字段"
            raise DialogueStaticCheckException("condition_group", reason, node.node_name)

        operator_options = ["==", "!=", ">", "<", "<=", ">=", "like", "isNull", "isNotNull"]
        if condition["operator"] not in operator_options:
            reason = "condition_group字段中operator字段必须是{}其中之一。而现在是{}".format(operator_options, condition["operator"])

        type_options = ["intent", "entity", "global", "params"]
        if condition["type"] not in type_options:
            reason = "condition_group字段中type字段必须是{}其中之一，而现在是{}".format(type_options, condition["type"])
            raise DialogueStaticCheckException("condition_group", reason, node.node_name)

        if condition["type"] in type_options[1:] and "value" not in condition:
            reason = "condition_group字段中如果条件判断类型为{}，则必须指定value字段".format(condition["type"])

    @staticmethod
    def start_node_conditional_checker(node: StartNode, value: List[Dict[str, Any]]) -> None:
        if not isinstance(value, list):
            reason = "slots字段的类型必须是list，而现在是{}".format(type(value))
            raise DialogueStaticCheckException("slots", reason, node.node_name)

        for group in value:
            if not isinstance(group, list):
                reason = "condition_group字段中每个group的类型必须是list，目前是{}".format(type(group))

            for condition in group:
                StartNode._check_condition(node, condition)

    required_checkers: Dict[str, Callable] = dict(condition_group=start_node_conditional_checker)

    traceback_template: Dict[str, Any] = {
        "type": "start",
        "node_name": "",
        "graph_name": "",
        "version": "",
        "global": {},
        "trigger_method": "意图及参数触发",
        "condition_group": None,
    }

    def call(self, context: StateTracker) -> ForwardIterator:
        context.update_traceback_datas(
            {
                "graph_name": context.agent.get_graph_meta_by_id(context.current_graph_id, "name"),
                "version": context.agent.get_graph_meta_by_id(context.current_graph_id, "version"),
                "global": context.params,
                "condition_group": self.config["condition_group"],
            }
        )
        context.set_is_start()
        return ForwardIterator(self, context)

    def trigger(self, context: StateTracker) -> bool:
        conditions = self.config["condition_group"]
        return self._judge_branch(context, conditions)
