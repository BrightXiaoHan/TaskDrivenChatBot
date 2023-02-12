"""
流程跳转节点
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from xiaoyu.dialogue.nodes.base import (
    BaseIterator,
    BaseNode,
    optional_value_checker,
    simple_type_checker,
)

if TYPE_CHECKING:
    from xiaoyu.dialogue.context import StateTracker

__all__ = ["SwitchNode"]


class SwitchNodeIterator(BaseIterator):
    async def run_state_1(self) -> Optional[str]:
        if self.config["jump_type"] == "3":
            graph_name = "用户挂断"
        elif self.config["jump_type"] == "2":
            graph_name = "转人工"
        else:
            graph_name = self.context.agent.get_graph_meta_by_id(self.config["graph_id"], "name")
        self.context.update_traceback_datas({"jump_type": ["jump_type"], "graph_name": graph_name})

        if self.config["jump_type"] not in ["2", "3"]:
            self.next_node = self.context.switch_graph(self.config["graph_id"], self.config["node_name"])
        return self.end()

    async def run_state_0(self) -> str:
        msg = self.context.latest_msg()
        # 用户挂断
        if self.config["jump_type"] == "3":
            self.context.is_end = True
            self.context.dialog_status = "20"
        # 主动转人工
        elif self.config["jump_type"] == "2":
            self.context.is_end = True
            # 这里判断逻辑是这样的，如果是由意图理解进入到转人工，understanding一定为“0”此时可以判断是主动转人工状态10
            # 反之则是系统转仍工状态码11
            self.context.dialog_status = "10" if msg.understanding == "0" else "11"

        if "jump_reply" in self.config:
            self.context.update_traceback_data("reply", self.config["jump_reply"])
            self.state = 1
            return self.config["jump_reply"]
        return await self.run_state_1()


class SwitchNode(BaseNode):
    NODE_NAME = "流程跳转节点"

    required_checkers: Dict[str, Callable] = dict(
        jump_type=optional_value_checker("jump_type", ["1", "2", "3"])
    )  # 1表示跳转到流程，2表示转人工，3表示挂机

    optional_checkers: Dict[str, Callable] = dict(
        jump_reply=simple_type_checker("jump_reply", str),
        graph_id=simple_type_checker("graph_id", str),
    )

    traceback_template: Dict[str, Any] = {
        "type": "jump",
        "node_name": "",
        "jump_type": "",  # 1跳转到流程，2转人工，3用户主动挂断
        "graph_name": "",
        "reply": "",
    }

    def call(self, context: StateTracker) -> SwitchNodeIterator:
        return SwitchNodeIterator(self, context)
