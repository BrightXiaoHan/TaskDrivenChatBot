"""
流程跳转节点
"""
from backend.dialogue.nodes.base import (
    _BaseNode,
    simple_type_checker,
    optional_value_checker,
)

__all__ = ["SwitchNode"]


class SwitchNode(_BaseNode):
    NODE_NAME = "流程跳转节点"

    required_checkers = dict(jump_type=optional_value_checker("jump_type", ["1", "2"]))  # 1表示跳转到流程，2表示转人工

    optional_checkers = dict(
        jump_reply=simple_type_checker("jump_reply", str),
        graph_id=simple_type_checker("graph_id", str),
    )

    def __call__(self, context):
        if self.config["jump_type"] == "2":
            context.is_end = True
            context.transfer_manual = True
        if "jump_reply" in self.config:
            yield self.config["jump_reply"]
        yield context.switch_graph(self.config["graph_id"], self.config["node_name"])
