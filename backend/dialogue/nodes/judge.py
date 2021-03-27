"""
判断节点
"""
from backend.dialogue.nodes.base import _BaseNode
from utils.exceptions import DialogueRuntimeException

__all__ = ('JudgeNode')


class JudgeNode(_BaseNode):

    __name__ = "判断节点"

    def __call__(self, context):
        """
        判断接下来应该走哪个分支

        Return
            str: 分支的id
        """
        for branch in self.config["breachs"]:
            conditions = branch["conditions"]
            if self._judge_branch(context, conditions):
                branch_id = branch["branch_id"]
                if branch_id not in self.branch_child:
                    raise DialogueRuntimeException(
                        "分支 {} 没有与其连接的子节点",
                        context.robot_code,
                        self.config["node_name"]
                    )
                yield self.branch_child[branch_id]
                return

        # 如果所有分支都不符合，则走默认分支
        yield self.default_child
