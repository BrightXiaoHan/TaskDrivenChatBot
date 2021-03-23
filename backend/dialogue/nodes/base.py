"""
节点基类型
"""
from utils.exceptions import (DialogueRuntimeException,
                              ModelBrokenException)
from utils.define import MODEL_TYPE_DIALOGUE


class _BaseNode(object):
    """对话流程节点基类

    Attributes:
        config (dict): 节点配置信息
        default_child (_BaseNode): 默认连接的子节点
        intent_child (dict): key值为intent的id，value为子节点
        branch_child (dict): key值未分支的id，value为子节点 

    Nodes：
        判断子节点的优先级为intent_child > branch_child > default_child
    """

    def __init__(self, config):
        self.config = config
        self.default_child = None
        self.intent_child = {}
        self.branch_child = {}

    def add_child(self, node, branch_id=None, intent_id=None):
        """向当前节点添加子节点

        Args:
            node (_BaseNode): 子节点
            branch_id (str, optional): 判断分支的id. Defaults to None.
            intent_id (str, optional): 意图分支的id. Defaults to None.

        Nodes:
            branch_id，intent_id指定时两者只能选一
        """
        if branch_id and intent_id:
            raise ModelBrokenException(self.context.robot_code,
                                       self.context.graph["version"],
                                       MODEL_TYPE_DIALOGUE,
                                       "节点{}与节点{}间的连接线不能同时配置branch_id与intent_id".format(
                                           self.config["node_name"], node.config["node_name"]))
        elif not branch_id and not intent_id:
            self.default_child = node
        elif branch_id:
            self.branch_child[branch_id] = node
        else:
            self.intent_child[intent_id] = node


class _TriggerNode(_BaseNode):

    def trigger(self):
        """
        判断该节点是否会被触发，子类必须复写该方法

        Return:
            bool: 触发为True，没有触发为False
        """
        raise NotImplementedError
