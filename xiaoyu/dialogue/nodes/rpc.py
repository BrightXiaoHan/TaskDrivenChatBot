"""
远程调用节点
"""
from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable, Dict, List

from xiaoyu.dialogue.nodes.base import (
    BaseIterator,
    BaseNode,
    optional_value_checker,
    simple_type_checker,
)
from xiaoyu.utils.exceptions import DialogueStaticCheckException
from xiaoyu.utils.funcs import async_get_rpc, async_post_rpc

if TYPE_CHECKING:
    from xiaoyu.dialogue.context import StateTracker

__all__ = ["RPCNode"]


class RPCNodeIterator(BaseIterator):
    def __init__(self, node: BaseNode, context: StateTracker):
        super().__init__(node, context)
        self.repeat_times = 1

    async def run_state_0(self) -> str:
        if self.repeat_times > 0:
            url = self.node.config["url"]
            headers = self.node.config.get("headers", None)
            params = {key: self.context.decode_ask_words(value) for key, value in self.node.config["params"].items()}
            method = self.node.config["method"].upper()
            if method == "POST":
                data = await async_post_rpc(url, params, data_type="params", headers=headers)
            else:
                data = await async_get_rpc(url, params, headers=headers)

            # 这里是一个补丁， 欧工想外部调用接口的faq返回是否理解的标志，这里做一下判断。
            if "understanding" in data:
                msg = self.context.latest_msg()
                msg.intent_confidence = 1 if data["understanding"] else 0
                if not data["understanding"]:
                    self.context.is_end = True
                    msg.understanding = "3"  # 未匹配到faq问题
                    msg.dialog_status = "11"  # 这里未识别的情况下做转人工处理 (欧工暂时是这么定的)

            # 这里是一个补丁，欧工想让掉用faq时rpc节点可以进行澄清、循环
            # 这里写死一个参数，如果rpc节点返回该参数就进行循环
            if data.get("__repeat", False):
                self.repeat_times -= 1
                return data["answer"]

        slots = {}
        for item in self.config["slots"]:
            slot = item["slot_name"]
            # TODO 这里做兼容处理，如果没有slot_alias字段，则使用slot_name
            slot_alias = item.get("slot_alias", slot)
            field = item["response_field"]
            if field in data:
                slots[slot] = data.get(field)
            elif "data" in data and field in data["data"]:
                # 这里也支持返回的json里面嵌套一层"data"字段，"data"字段里面的内容是需要的内容
                slots[slot] = data["data"].get(field)
            else:
                slots[slot] = ""
            self.context.fill_slot(slot, slots[slot], slot_alias)

        # 记录调试信息
        self.context.update_traceback_datas(
            {
                "header": headers,
                "method": method,
                "url": url,
                "params": params,
                "response": data,
                "slots": slots,
            }
        )

        if self.default_child:
            self.context.add_traceback_data(
                {
                    "type": "conn",
                    "line_id": self.line_id_mapping[self.default_child.node_name],
                    "conn_type": "default",
                    "source_node_name": self.node_name,
                    "target_node_name": self.default_child.node_name,
                }
            )
        self.next_node = self.node.default_child
        return self.end()


class RPCNode(BaseNode):
    NODE_NAME = "函数节点"

    def rpc_node_slots_checker(node: RPCNode, slots: List[Dict[str, Any]]):
        if not isinstance(slots, list):
            reason = "slots字段的类型必须是list，而现在是{}".format(type(slots))
            raise DialogueStaticCheckException("slots", reason=reason, node_id=node.node_name)

        for slot in slots:
            if "slot_name" not in slot:
                reason = "slots字段中的每个元素必须要有slot_name字段"
                raise DialogueStaticCheckException("slots", reason=reason, node_id=node.node_name)

            if "response_field" not in slot:
                reason = "slots字段中的每个元素必须要有response_filed字段"
                raise DialogueStaticCheckException("slots", reason=reason, node_id=node.node_name)

    required_checkers: Dict[str, Callable] = OrderedDict(
        protocal=optional_value_checker("protocal", ["http", "https"]),
        method=optional_value_checker("method", ["get", "post"]),
        url=simple_type_checker("url", str),
    )
    optional_checkers: Dict[str, Callable] = OrderedDict(
        headers=simple_type_checker("headers", dict),
        params=simple_type_checker("params", dict),
        slots=rpc_node_slots_checker,
    )

    traceback_template: Dict[str, Any] = {
        "type": "fun",
        "node_name": "",
        "header": {},
        "method": "",
        "url": "",
        "params": {},
        "response": {},
        "slots": {},
    }

    def call(self, context: StateTracker) -> RPCNodeIterator:
        return RPCNodeIterator(self, context)
