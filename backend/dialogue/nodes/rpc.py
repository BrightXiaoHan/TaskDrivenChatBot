"""
远程调用节点
"""
from backend.dialogue.nodes.base import _BaseNode
from utils.funcs import get_rpc, post_rpc
from utils.exceptions import RpcException

__all__ = ['RPCNode']


class RPCNode(_BaseNode):
    NODE_NAME = "函数节点"

    def __call__(self, context):
        url = self.config["url"]
        headers = self.config.get("headers", None)
        params = {
            key: context.decode_ask_words(value)
            for key, value in self.config["params"].items()
        }
        if self.config["method"] == "POST":
            data = post_rpc(url, params, data_type="params", headers=headers)
        else:
            data = get_rpc(url, params, headers=headers)

        if "data" not in data:
            raise RpcException(url, params, str(data))

        data = data["data"]
        for item in self.config["slots"]:
            slot = item["slot_name"]
            field = item["response_field"]
            context.fill_slot(slot, data.get(field, None))

        yield self.default_child
