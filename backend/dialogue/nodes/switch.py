"""
流程跳转节点
"""
from backend.dialogue.nodes.base import _BaseNode

__all__ = ["SwitchNode"]


class SwitchNode(_BaseNode):
    __name__ = "流程跳转节点"

    def __call__(self, context):
        context.switch_graph(self.config["graph_id"])
        yield None
