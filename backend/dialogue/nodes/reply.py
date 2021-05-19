"""
回复节点
"""
from backend.dialogue.nodes.base import _BaseNode

__all__ = ["ReplyNode"]


class ReplyNode(_BaseNode):
    NODE_NAME = '回复节点'

    def __call__(self, context):
        # TODO 这里目前暂时这么判断，回复节点如果没有子节点则判断本轮对话结束
        if not self.default_child:
            context.is_end = True
        yield self.config["content"]
        yield from self.forward(context)
