"""
远程调用节点
"""
from backend.dialogue.nodes.base import _BaseNode
from utils.funcs import get_rpc, post_rpc

__all__ = ['RPCNode']


class RPCNode(_BaseNode):
    __name__ = "函数节点"

    def __call__(self, context):
        url = "{}://{}".format(self.config["protocal"], self.config["url"])
        headers = self.config["headers"]
        params = {
            key: self.decode_ask_words(value) for key, value in self.config["params"]
        }
        if self.config["method"] == "POST":
            data = post_rpc(url, params, data_type="params", headers=headers)
        else:
            data = get_rpc(url, params, headers=headers)

        for item in self.config["slots"]:
            slot = item["slot_name"]
            field = item["response_field"]
            context.fill_slot(slot, data.get(field, None))

        yield self.get_child()
