"""
机器人说节点
"""
import random

from backend.dialogue.nodes.base import (_BaseNode, callback_cycle_checker,
                                         simple_type_checker)
from backend.dialogue.nodes.judge import _check_condition
from utils.exceptions import DialogueStaticCheckException

__all__ = ["RobotSayNode"]


def say_node_conditional_checker(node, branchs):
    if not isinstance(branchs, list):
        reason = "branchs字段的类型必须是list，而现在是{}".format(type(branchs))
        raise DialogueStaticCheckException(
            "branchs", reason=reason, node_id=node.node_name
        )

    for branch in branchs:
        if not isinstance(branch, dict):
            reason = "branchs字段中每个branch的类型必须是dict，目前是{}".format(type(branch))
            raise DialogueStaticCheckException(
                "branchs", reason, node_id=node.node_name
            )

        if "conditions" not in branch or not isinstance(branch["conditions"], list):
            reason = "branchs字段中的每个group必须有conditions字段，并且是list类型"
            raise DialogueStaticCheckException(
                "branchs", reason, node_id=node.node_name
            )

        if "content" not in branch or not isinstance(branch["content"], list):
            reason = "branchs字段中的每个group必须有content字段，并且是list类型"
            raise DialogueStaticCheckException(
                "branchs", reason, node_id=node.node_name
            )

        for condition in branch["conditions"]:
            if not isinstance(condition, list):
                reason = "branchs字段中每个group的conditions字段必须是list，而现在是{}".format(
                    type(condition)
                )
                raise DialogueStaticCheckException(
                    "slots", reason=reason, node_id=node.node_name
                )

            for group in condition:
                _check_condition(node, group)


class RobotSayNode(_BaseNode):
    NODE_NAME = "机器人说节点"

    optional_checkers = dict(
        life_cycle=callback_cycle_checker(),
        callback_words=callback_cycle_checker(),
        branchs=say_node_conditional_checker,
        content=simple_type_checker("content", list),
    )

    traceback_template = {"type": "robotSay", "node_name": "", "is_end": False}

    def static_check(self):
        super().static_check()
        if "branchs" not in self.config and "content" not in self.config:
            raise DialogueStaticCheckException(
                "content, branchs",
                "机器人说节点必须配置branchs或者content字段",
                node_id=self.node_name,
            )

    async def call(self, context):
        # TODO 这里目前暂时这么判断，回复节点如果没有子节点则判断本轮对话结束
        if not self.default_child:
            context.is_end = True
            context.dialog_status = "20"  # 此处为机器人挂断的状态码
            # 记录调试信息
            context.update_traceback_data("is_end", True)

        # 如果回复节点包含选项，则将选项添加到当前message里面
        options = self.config.get("options", [])
        msg = context._latest_msg()
        msg.options = options

        has_answer = False  # 机器人是否已经回答
        if "branchs" in self.config:
            # 否则进入条件判断，根据不通条件生成不通的回复话术
            for branch in self.config["branchs"]:
                if "conditions" not in branch:
                    continue
                conditions = branch["conditions"]
                if self._judge_branch(context, conditions):
                    yield random.choice(branch["content"])
                    has_answer = True
                    break

        if "content" in self.config and not has_answer:
            # 如果配置的回复话术为固定的一个字符串
            yield random.choice(self.config["content"])

        if bool(self.option_child):
            for item in self.options(context):
                yield item
        else:
            async for item in self.forward(
                context, life_cycle=self.config.get("life_cycle", 0)
            ):
                yield item
