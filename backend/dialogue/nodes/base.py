"""
节点基类型
"""
from itertools import chain
from backend.dialogue.nodes.builtin import builtin_intent
from utils.exceptions import DialogueRuntimeException, DialogueStaticCheckException


def simple_type_checker(key, dtype):

    def get_class_name(cls):
        return cls.__name__

    def check(node, value):
        if not isinstance(value, dtype):
            reason = "字段{}的值必须是类型{}，" \
                "但是配置的类型是{}。".format(key, get_class_name(
                    dtype), get_class_name(type(value)))
            raise DialogueStaticCheckException(key, reason, node.node_name)
    return check


def optional_value_checker(key, ref_values):

    def check(node, value):
        if value not in ref_values:
            reason = "字段key的值必须是{}中的值之一," \
                " 而不是{}。".format(ref_values, value)
            raise DialogueStaticCheckException(key, reason, node.node_name)

    return check


def empty_checker():
    def check(*_):
        return None
    return check


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
    # 节点类别的名称
    NODE_NAME = "基类节点"

    base_checkers = dict(
        node_id=simple_type_checker("node_id", str),
        node_name=simple_type_checker("node_name", str),
        node_type=empty_checker(),
    )
    required_checkers = {}
    optional_checkers = {}

    def __init__(self, config):
        self.config = config
        self.default_child = None
        self.intent_child = {}
        self.branch_child = {}
        self.option_child = {}

    @property
    def node_name(self):
        """
        获取用户定义的节点的名称, 注意与NODE_NAME的区别。
        """
        return self.config.get("node_name", "unknown")
        

    def static_check(self):
        """
        静态检查配置的数据结构
        """
        required_checkers = chain(
            self.base_checkers.items(), self.required_checkers.items())
        for key, func in required_checkers:
            if key in self.config:
                func(self, self.config[key])
            else:
                raise DialogueStaticCheckException(key, "该节点缺少此必填字段", self.node_name)

        for key, func in self.optional_checkers.items():
            if key in self.config:
                func(self, self.config[key])

    def add_child(self, node, branch_id=None, intent_id=None, option_id=None):
        """向当前节点添加子节点

        Args:
            node (_BaseNode): 子节点
            branch_id (str, optional): 判断分支的id. Defaults to None.
            intent_id (str, optional): 意图分支的id. Defaults to None.
            option_id (str, optional): 用户选项分支的id. Default to None.

        Nodes:
            branch_id，intent_id, option_id指定时三者只能选一
        """
        if option_id:
            self.option_child[option_id] = node
        elif branch_id:
            self.branch_child[branch_id] = node
        elif intent_id:
            self.intent_child[intent_id] = node
        else:
            self.default_child = node

    def _judge_condition(self, context, condition):
        msg = context._latest_msg()
        type = condition["type"]
        operator = condition["operator"]
        if operator not in ["==", "!="]:
            raise DialogueRuntimeException(
                "分支判断条件中operator字段必须是==，!=其中之一",
                context.robot_code,
                self.config["node_name"]
            )
        if type == "intent":
            if not msg:
                return False
            # 如果配置有内置识别能力，则使用内置识别能力进行识别。TODO这里是否有重复识别的问题？
            if condition["value"] in builtin_intent:
                builtin_intent[condition["value"]].on_process_msg(msg)
            if operator == "==":
                return msg.intent == condition["value"]
            else:
                return msg.intent != condition["value"]
        elif type == "entity":
            if not msg:
                return False
            entities = msg.get_abilities()
            target = entities.get(condition["name"], [])
            if operator == "==":
                return condition["value"] in target
            else:
                return condition["value"] not in target
        elif type == "global":
            target = context.slots.get(condition["name"])
            if operator == "==":
                return target == condition["value"]
            else:
                return target != condition["value"]
        elif type == "params":
            target = context.params.get(condition["name"])
            if operator == "==":
                return target == condition["value"]
            else:
                return target != condition["value"]
        else:
            raise DialogueRuntimeException(
                "条件判断type字段必须是intent，entity，global, params其中之一",
                context.robot_code,
                self.config["node_name"])

    def _judge_branch(self, context, conditions):
        for condition in conditions:
            result = True
            for item in condition:
                result = result and self._judge_condition(context, item)
            if result:
                return True
        return False

    def forward(self, context, use_default=True):
        """
        意图决定下一个节点的走向
        """
        msg = context._latest_msg()
        # 根据当前节点连接线配置的意图重新进行识别

        # 如果配置了内置意图，做一下识别
        for target_intent in self.intent_child:
            if target_intent in builtin_intent:
                intent = builtin_intent[target_intent].on_process_msg(msg)

        msg.update_intent(self.intent_child)
        intent = msg.intent

        if intent in self.intent_child:
            yield self.intent_child[intent]
        else:
            if use_default:  # 判断其他意图是否跳转
                yield self.default_child

    def options(self, context):
        """
        选项决定下一个节点的走向
        """
        msg = context._latest_msg()
        option_node = self.option_child.get(msg.text, None)

        if option_node:
            yield option_node
        else:
            raise DialogueRuntimeException("没有找到该选项{}".format(msg.text), context.robot_code, self.node_name)


class _TriggerNode(_BaseNode):

    def trigger(self):
        """
        判断该节点是否会被触发，子类必须复写该方法

        Return:
            bool: 触发为True，没有触发为False
        """
        raise NotImplementedError
