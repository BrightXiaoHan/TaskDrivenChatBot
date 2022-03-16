"""
节点基类型
"""
import random
from copy import deepcopy
from functools import reduce
from itertools import chain
from backend.dialogue.nodes.builtin import builtin_intent
from backend.dialogue.nodes.hard_code import hard_code_intent
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

def callback_cycle_checker():

    def check(node, _):
        callback_in = "callback_words" in node.config
        life_cycle_in = "life_cycle" in node.config

        if life_cycle_in and not callback_in or (not life_cycle_in and callback_in):
            reason = "节点类型{}的配置中必须同时包含或者同时不包含callback_words和life_cycle两个字段。".format(node.NODE_NAME)
            raise DialogueStaticCheckException("callback_words, life_cycle", reason, node.node_name)

        if life_cycle_in and callback_in:
            simple_type_checker("callback_words", list)(node, node.config["callback_words"])
            simple_type_checker("life_cycle", int)(node, node.config["life_cycle"])

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

    # 此属性必须被子类复写
    traceback_template = {}

    def __init__(self, config):
        self.config = config
        self.default_child = None
        self.intent_child = {}
        self.branch_child = {}
        self.option_child = {}

        self.line_id_mapping = {}

    @property
    def node_name(self):
        """
        获取用户定义的节点的名称, 注意与NODE_NAME的区别。
        """
        return self.config.get("node_name", "unknown")

    async def __call__(self, context):
        traceback_data = deepcopy(self.traceback_template)
        traceback_data["node_name"] = self.node_name
        context.add_traceback_data(traceback_data)
        async for item in self.call(context):
            yield item
    
    async def call(self, context):
        raise NotImplementedError

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

    def add_child(self, node, line_id, branch_id=None, intent_id=None, option_id=None):
        """向当前节点添加子节点

        Args:
            node (_BaseNode): 子节点
            branch_id (str, optional): 判断分支的id. Defaults to None.
            intent_id (str, optional): 意图分支的id. Defaults to None.
            option_id (str, optional): 用户选项分支的id. Default to None.

        Nodes:
            branch_id，intent_id, option_id指定时三者只能选一
        """
        self.line_id_mapping[node.node_name] = line_id
        if option_id:
            self.option_child[option_id] = node
        elif branch_id:
            self.branch_child[branch_id] = node
        elif intent_id:
            self.intent_child[intent_id] = node
        else:
            self.default_child = node

    def _eval(self, source, target, operator):
        """
        判断source与target是否符合operator的条件
        """
        if isinstance(target, (list, tuple)):
            return reduce(lambda x, y: x or y, map(lambda x: self._eval(source, x), target))
        else:
            # 这些操作符必须是字符串之间进行操作
            if operator == "==":
                return str(source) == str(target)
            if operator == "!=":
                return str(source) != str(target)
            if operator == "like":
                return str(source) in str(target)
            if operator == "isNull":
                return bool(source)
            if operator == "notNull":
                return not bool(source)

            # 这些操作符必须是数字类型之间操作
            if operator == ">":
                return source > target
            if operator == "<":
                return source < target
            if operator == ">=":
                return source >= target
            if operator == "<=":
                return source <= target
            return False

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
            return self._eval(msg.intent, condition["value"], operator)
        elif type == "entity":
            if not msg:
                return False
            entities = msg.get_abilities()
            target = entities.get(condition["name"], [])
            return self._eval(target, condition["value"], operator)
        elif type == "global":
            # 这里防止某些实体被设置成int类型，这里统一转换成字符串进行比较
            target = str(context.slots.get(condition["name"]))
            return self._eval(target, condition["value"], operator)
        elif type == "params":
            target = context.params.get(condition["name"])
            return self._eval(target, condition["value"], operator)
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

    async def forward(self, context, use_default=True, life_cycle=0):
        """
        意图决定下一个节点的走向
        """
        msg = context._latest_msg()
        # 根据当前节点连接线配置的意图重新进行识别

        # 如果配置了内置意图，做一下识别
        for target_intent in self.intent_child:
            if target_intent in builtin_intent:
                intent = builtin_intent[target_intent].on_process_msg(msg)
            if target_intent in hard_code_intent:
                intent = hard_code_intent[target_intent].on_process_msg(msg, self)
        # TODO  这里是个坑，这里打下补丁。这里保存原始的intent，如果下一个触发节点为None，则流程结束，需要保存原来的intent
        origin_intent = msg.intent
        msg.update_intent_by_candidate(self.intent_child)
        intent = msg.intent

        if intent in self.intent_child:
            next_node = self.intent_child[intent]
            context.add_traceback_data({
                "line_id": self.line_id_mapping[next_node.node_name],
                "type": "conn",
                "conn_type": "intent",
                "source_node_name": self.node_name,
                "target_node_name": next_node.node_name,
                "intent_name": msg.get_intent_name_by_id(intent),
                "match_type": "model",  # TODO 这里没有完成，需要做进一步判断
                "match_words": ""  # TODO 这里没有完成，需要进一步做判断
            })
            if not next_node:
                msg.intent = origin_intent
            yield next_node
        else:
            msg.understanding = "1"
            if use_default:  # 判断其他意图是否跳转
                next_node = self.default_child
                if not next_node:
                    msg.intent = origin_intent
                if life_cycle > 0:
                    if len(msg.faq_result["title"]) < len(msg.text) * 2 and len(
                        msg.faq_result["title"]) * 2 > len(msg.text):
                        yield msg.get_faq_answer() + "\n" + random.choice(self.config["callback_words"])
                    else:
                        yield random.choice(self.config["callback_words"])
                    async for item in self.forward(context, life_cycle=life_cycle-1):
                        yield item
                else:
                    if next_node:
                        context.add_traceback_data({
                            "line_id": self.line_id_mapping[next_node.node_name],
                            "type": "conn",
                            "conn_type": "default",
                            "source_node_name": self.node_name,
                            "target_node_name": next_node.node_name
                        })
                    yield next_node

    def options(self, context):
        """
        选项决定下一个节点的走向
        """
        msg = context._latest_msg()
        option_node = self.option_child.get(msg.text, None)

        if option_node:
            context.add_traceback_data({
                "line_id": self.line_id_mapping[option_node.node_name],
                "conn_type": "option",
                "type": "conn",
                "source_node_name": self.node_name,
                "target_node_name": option_node.node_name,
                "option_name": msg.text,
                "option_list": list(self.option_child.keys())
            })
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
