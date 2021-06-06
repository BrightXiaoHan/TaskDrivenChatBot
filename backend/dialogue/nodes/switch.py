"""
流程跳转节点
"""
from backend.dialogue.nodes.base import _BaseNode, simple_type_checker

__all__ = ["SwitchNode"]


class SwitchNode(_BaseNode):
    NODE_NAME = "流程跳转节点"
    required_checkers = dict(
        graph_id=simple_type_checker("graph_id", str),
    )
    def __call__(self, context):
        yield context.switch_graph(self.config["graph_id"], self.config["node_name"])
