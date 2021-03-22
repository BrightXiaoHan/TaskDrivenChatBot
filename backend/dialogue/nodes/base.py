"""
节点基类型
"""
from utils.exceptions import DialogueRuntimeException


class _BaseNode(object):
    def __init__(self, config):
        self.config = config
        self.child = {}

    def add_child(self, node, branch_id="default"):
        self.child[branch_id] = node

    def get_child(self, branch_id="default"):
        return self.child.get(branch_id, None)


class _TriggerNode(_BaseNode):

    def trigger(self):
        """
        判断该节点是否会被触发，子类必须复写该方法

        Return:
            float: 触发置信概率，0-1
        """
        raise NotImplementedError


class _MultiBranchNode(object):

    def choose(self, context):
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
                return branch["branch_id"]

        # 如果所有分支都不符合，则走默认分支
        return "default"
