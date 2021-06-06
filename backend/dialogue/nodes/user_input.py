"""
用户输入节点
"""
from backend.dialogue.nodes.base import _TriggerNode, simple_type_checker
from utils.exceptions import DialogueStaticCheckException

__all__ = ["UserInputNode"]


def _check_condition(condition):
    if "type" not in condition:
        reason = "condition_group字段中每个判断条件必须有type字段"
        raise DialogueStaticCheckException("condition_group", reason)

    if "operator" not in condition:
        reason = "condition_group字段中每个判断条件必须有operator字段"
        raise DialogueStaticCheckException("condition_group", reason)

    operator_options = ["==", "!="]
    if condition["operator"] not in operator_options:
        reason = "condition_group字段中operator字段必须是{}其中之一。而现在是{}".format(
            operator_options, condition["operator"])

    type_options = ["intent", "entity", "global", "params"]
    if condition["type"] not in type_options:
        reason = "condition_group字段中type字段必须是{}其中之一，而现在是{}".format(
            type_options, condition["type"])
        raise DialogueStaticCheckException("condition_group", reason)

    if condition["type"] in type_options[1:] and "value" not in condition:
        reason = "condition_group字段中如果条件判断类型为{}，则必须指定value字段".format(
            condition["type"])


def user_input_node_conditional_checker(_, value):
    if not isinstance(value, list):
        reason = "slots字段的类型必须是list，而现在是{}".format(type(value))
        raise DialogueStaticCheckException("slots", reason=reason)

    for group in value:
        if not isinstance(group, list):
            reason = "condition_group字段中每个group的类型必须是list，目前是{}".format(
                type(group))

        for condition in group:
            _check_condition(condition)


class UserInputNode(_TriggerNode):
    NODE_NAME = "用户输入节点"

    required_checkers = dict(
        life_cycle=simple_type_checker("life_cycle", int),
        condition_group=user_input_node_conditional_checker
    )

    def __call__(self, context):
        yield from self.forward(context)

    def trigger(self, context):
        conditions = self.config["condition_group"]
        return self._judge_branch(context, conditions)
