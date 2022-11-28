"""
远程调用节点
"""
from collections import OrderedDict

from backend.dialogue.nodes.base import (_BaseNode, optional_value_checker,
                                         simple_type_checker)
from utils.exceptions import DialogueStaticCheckException
from utils.funcs import async_get_rpc, async_post_rpc

__all__ = ["RPCNode"]


def rpc_node_slots_checker(node, slots):
    if not isinstance(slots, list):
        reason = "slots字段的类型必须是list，而现在是{}".format(type(slots))
        raise DialogueStaticCheckException(
            "slots", reason=reason, node_id=node.node_name
        )

    for slot in slots:
        if "slot_name" not in slot:
            reason = "slots字段中的每个元素必须要有slot_name字段"
            raise DialogueStaticCheckException(
                "slots", reason=reason, node_id=node.node_name
            )

        if "response_field" not in slot:
            reason = "slots字段中的每个元素必须要有response_filed字段"
            raise DialogueStaticCheckException(
                "slots", reason=reason, node_id=node.node_name
            )


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
        slots=rpc_node_slots_checker,
    )

    traceback_template = {
        "type": "fun",
        "node_name": "",
        "header": {},
        "method": "",
        "url": "",
        "params": {},
        "response": {},
        "slots": {},
    }

    async def call(self, context):
        for _ in range(2):
            url = self.config["url"]
            headers = self.config.get("headers", None)
            params = {
                key: context.decode_ask_words(value)
                for key, value in self.config["params"].items()
            }
            method = self.config["method"].upper()
            if method == "POST":
                data = await async_post_rpc(
                    url, params, data_type="params", headers=headers
                )
            else:
                data = await async_get_rpc(url, params, headers=headers)

            # 这里是一个补丁， 欧工想外部调用接口的faq返回是否理解的标志，这里做一下判断。
            if "understanding" in data:
                msg = context._latest_msg()
                msg.intent_confidence = 1 if data["understanding"] else 0
                if not data["understanding"]:
                    context.is_end = True
                    msg.understanding = "3"  # 未匹配到faq问题
                    msg.dialog_status = "11"  # 这里未识别的情况下做转人工处理 (欧工暂时是这么定的)

            # 这里是一个布丁，欧工想让掉用faq时rpc节点可以进行澄清、循环
            # 这里写死一个参数，如果rpc节点返回该参数就进行循环
            if data.get("__repeat", False):
                yield data["answer"]
            else:
                break

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
            context.fill_slot(slot, slots[slot], slot_alias)

        # 记录调试信息
        context.update_traceback_datas(
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
            context.add_traceback_data(
                {
                    "type": "conn",
                    "line_id": self.line_id_mapping[self.default_child.node_name],
                    "conn_type": "default",
                    "source_node_name": self.node_name,
                    "target_node_name": self.default_child.node_name,
                }
            )
        yield self.default_child
