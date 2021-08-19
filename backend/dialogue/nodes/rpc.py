"""
远程调用节点
"""
import logging
from collections import OrderedDict

from backend.dialogue.nodes.base import (_BaseNode,
                                         simple_type_checker,
                                         optional_value_checker)
from utils.funcs import get_rpc, post_rpc
from utils.exceptions import RpcException, DialogueStaticCheckException

__all__ = ['RPCNode']
logger = logging.getLogger('RpcNode')

def rpc_node_slots_checker(node, slots):
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


class RPCNode(_BaseNode):
    NODE_NAME = "函数节点"

    required_checkers = OrderedDict(
        protocal=optional_value_checker("protocal", ["http", "https"]),
        method=optional_value_checker("method", ["get", "post"]),
        url=simple_type_checker("url", str),
    )
    optional_checkers = OrderedDict(
        headers=simple_type_checker("headers", dict),
        params=simple_type_checker("params", dict),
        slots=rpc_node_slots_checker
    )

    def __call__(self, context):
        url = self.config["url"]
        headers = self.config.get("headers", None)
        params = {
            key: context.decode_ask_words(value)
            for key, value in self.config["params"].items()
        }
        if self.config["method"].upper() == "POST":
            data = post_rpc(url, params, data_type="params", headers=headers)
        else:
            data = get_rpc(url, params, headers=headers)
        
        logger.info({
            "url": url,
            "params": params,
            "response": data
        })

        # 这里是一个补丁， 欧工想外部调用接口的faq返回是否理解的标志，这里做一下判断。
        if "understanding" in data:
            msg = context._latest_msg()
            msg.intent_confidence = 1 if data["understanding"] else 0

        for item in self.config["slots"]:
            slot = item["slot_name"]
            field = item["response_field"]
            context.fill_slot(slot, data.get(field, None))

        yield self.default_child
