"""
流程跳转节点
"""
from backend.dialogue.nodes.base import _BaseNode

__all__ = ["SwitchNode"]


class SwitchNode(_BaseNode):
    NODE_NAME = "流程跳转节点"

    def __call__(self, context):
        yield context.switch_graph(self.config["graph_id"], self.config["node_name"])
