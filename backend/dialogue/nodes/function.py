"""
函数调用节点 TODO
"""
from backend.dialogue.nodes.base import (_BaseNode,
                                         optional_value_checker,
                                         simple_type_checker)
from utils.exceptions import DialogueRuntimeException

__all__ = ["FunctionNode"]


class FunctionNode(_BaseNode):
    NODE_NAME = "服务节点"

    required_checkers = dict(
        language=optional_value_checker("language", ["python", "sh", "nodejs"])
    )
    # TODO checker implement here

    def __call__(self, context):
        language = self.config["language"]
        if language == "python":
            # TODO python implement
            pass
        else:
            raise DialogueRuntimeException("不支持的调用类型{}".format(language),
                                           context.robot_code,
                                           self.config["node_name"])
