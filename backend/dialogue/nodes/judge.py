"""
判断节点
"""
from backend.dialogue.nodes.base import _BaseNode
from utils.exceptions import DialogueRuntimeException


class JudgeNode(_BaseNode):

    def __call__(self, context):
        """
        判断接下来应该走哪个分支

        Return
            str: 分支的id
        """
        msg = context._latest_msg()

        def judge_branch(branch):
            conditions = branch["conditions"]
            for condition in conditions:
                result = True
                for item in condition:
                    result = result and judge_condition(item)
                if result:
                    return True
            return False

        def judge_condition(condition):
            type = condition["type"]
            operator = condition["operator"]
            if operator not in ["==", "!="]:
                raise DialogueRuntimeException(
                    "分支判断条件中operator字段必须是==，!=其中之一",
                    context.robot_code,
                    self.config["node_name"]
                )
            if type == "intent":
                if operator == "==":
                    return msg.intent == condition["value"]
                else:
                    return msg.intent != condition["value"]
            elif type == "entity":
                entities = msg.get_abilities()
                target = entities.get(condition["entity_name"], [])
                if operator == "==":
                    return condition["value"] in target
                else:
                    return condition["value"] not in target
            elif type == "global":
                target = context.slots.get(condition["global_slot"])
                if operator == "==":
                    return target == condition["value"]
                else:
                    return target != condition["value"]
            else:
                raise DialogueRuntimeException(
                    "条件判断type字段必须是intent，entity，global其中之一",
                    context.robot_code,
                    self.config["node_name"])

        for branch in self.config["breachs"]:
            if judge_branch(branch):
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
