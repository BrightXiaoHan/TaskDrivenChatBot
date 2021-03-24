"""
函数调用节点 TODO
"""
from backend.dialogue.nodes.base import _BaseNode
from utils.exceptions import DialogueRuntimeException


class FunctionNode(_BaseNode):
    def __call__(self, context):
        language = self.config["language"]
        if language == "python":
            pass
        else:
            raise DialogueRuntimeException("不支持的调用类型{}".format(language),
                                           context.robot_code,
                                           self.config["node_name"])
