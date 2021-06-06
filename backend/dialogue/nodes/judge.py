"""
判断节点
"""
from backend.dialogue.nodes.base import _BaseNode
from utils.exceptions import DialogueRuntimeException, DialogueStaticCheckException

__all__ = ['JudgeNode']


def _check_condition(node, condition):
    if "type" not in condition:
        reason = "判断条件中每个判断条件必须有type字段"
        raise DialogueStaticCheckException("condition_group", reason, node.node_name)

    if "operator" not in condition:
        reason = "判断条件中每个判断条件必须有operator字段"
        raise DialogueStaticCheckException("condition_group", reason, node.node_name)

    operator_options = ["==", "!="]
    if condition["operator"] not in operator_options:
        reason = "判断条件中operator字段必须是{}其中之一。而现在是{}".format(
            operator_options, condition["operator"])
        raise DialogueStaticCheckException("condition_group", reason, node.node_name)

    type_options = ["intent", "entity", "global", "params"]
    if condition["type"] not in type_options:
        reason = "判断条件中中type字段必须是{}其中之一，而现在是{}".format(
            type_options, condition["type"])
        raise DialogueStaticCheckException("condition_group", reason, node.node_name)

    if condition["type"] in type_options[1:] and "value" not in condition:
        reason = "判断条件中如果条件判断类型为{}，则必须指定value字段".format(
            condition["type"])


def judge_node_conditional_checker(node, branchs):
    if not isinstance(branchs, list):
        reason = "branchs字段的类型必须是list，而现在是{}".format(type(branchs))
        raise DialogueStaticCheckException("branchs", reason=reason, node_id=node.node_name)

    for branch in branchs:
        if not isinstance(branch, dict):
            reason = "branchs字段中每个branch的类型必须是dict，目前是{}".format(
                type(branch))
            raise DialogueStaticCheckException("branchs", reason, node_id=node.node_name)

        if "branch_id" not in branch:
            reason = "branchs字段中的每个branch中必须有branch_id字段"
            raise DialogueStaticCheckException("branchs", reason, node_id=node.node_name)

        if "conditions" not in branch or not isinstance(branch["conditions"], list):
            reason = "branchs字段中的每个group必须有conditions字段，并且是list类型"
            raise DialogueStaticCheckException("branchs", reason, node_id=node.node_name)

        for condition in branch["conditions"]:
            if not isinstance(condition, list):
                reason = "branchs字段中每个group的conditions字段必须是list，而现在是{}".format(type(condition))
                raise DialogueStaticCheckException("slots", reason=reason, node_id=node.node_name)
        
            for group in condition:
                if not isinstance(branch, list):
                    reason = "condition_group字段中每个group的类型必须是list，目前是{}".format(
                        type(group))
        
                for item in group:
                    _check_condition(node, item)

class JudgeNode(_BaseNode):

    NODE_NAME = "判断节点"

    required_checkers = dict(
        branchs=judge_node_conditional_checker
    )

    def __call__(self, context):
        """
        判断接下来应该走哪个分支

        Return
            str: 分支的id
        """
        for branch in self.config["branchs"]:
            if "conditions" not in branch:
                continue
            conditions = branch["conditions"]
            if self._judge_branch(context, conditions):
                branch_id = branch["branch_id"]
                if branch_id not in self.branch_child:
                    raise DialogueRuntimeException(
                        "分支 {} 没有与其连接的子节点",
                        context.robot_code,
                        self.config["node_name"]
                    )
                yield self.branch_child[branch_id]
                return

        # 如果所有分支都不符合，则走默认分支
        yield self.default_child
