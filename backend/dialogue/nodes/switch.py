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

    traceback_template = {
        "type": "jump",
        "node_name": "",
        "jump_type": "",  # 1跳转到流程，2转人工
        "graph_name": "",
        "reply": ""
    }

    def call(self, context):
        if self.config["jump_type"] == "2":
            context.is_end = True
            context.transfer_manual = True
        if "jump_reply" in self.config:
            context.update_traceback_data("reply", self.config["jump_reply"])
            yield self.config["jump_reply"]

        if self.config["jump_type"] == "2":
            graph_name = "转人工"
        else:
            graph_name = context.agent.get_graph_meta_by_id(self.config["graph_id"], "name")
        context.update_traceback_datas({
            "jump_type": ["jump_type"],
            "graph_name": graph_name
        })

        if self.config["jump_type"] == "2":
            yield None
        else:
            yield context.switch_graph(self.config["graph_id"], self.config["node_name"])
