"""
机器人说节点
"""
import random
from backend.dialogue.nodes.base import _BaseNode, simple_type_checker, callback_cycle_checker

__all__ = ["RobotSayNode"]


class RobotSayNode(_BaseNode):
    NODE_NAME = "机器人说节点"

    required_checkers = dict(
        content=simple_type_checker("content", list)
    )

    optional_checkers = dict(
        life_cycle=callback_cycle_checker(),
        callback_words=callback_cycle_checker()
    )

    traceback_template = {
        "type": "robotSay",
        "node_name": "",
        "is_end": False
    }

    async def call(self, context):
        # TODO 这里目前暂时这么判断，回复节点如果没有子节点则判断本轮对话结束
        if not self.default_child:
            context.is_end = True
            context.dialog_status = "20"  # 此处为机器人挂断的状态码
            # 记录调试信息
            context.update_traceback_data("is_end", True)

        # 如果回复节点包含选项，则将选项添加到当前message里面
        options = self.config.get("options", [])
        msg = context._latest_msg()
        msg.options = options

        # 如果配置的回复话术为固定的一个字符串
        if isinstance(self.config["content"], str):
            yield self.config["content"]
        else:  # 如果配置的回复话术为list，则随机选择一个
            yield random.choice(self.config["content"])

        if bool(self.option_child):
            for item in self.options(context):
                yield item
        else:
            async for item in self.forward(
                context, life_cycle=self.config.get("life_cycle", 0)
            ):
                yield item
