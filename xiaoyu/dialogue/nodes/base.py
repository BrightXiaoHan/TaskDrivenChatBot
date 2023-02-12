"""
节点基类型
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from copy import deepcopy
from functools import reduce
from itertools import chain
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from xiaoyu.dialogue.context import FAQ_FLAG
from xiaoyu.nlu.builtin import builtin_intent
from xiaoyu.nlu.builtin.hard_code import hard_code_intent
from xiaoyu.nlu.interpreter import Message
from xiaoyu.utils.exceptions import (
    DialogueRuntimeException,
    DialogueStaticCheckException,
)
from xiaoyu.utils.funcs import levenshtein_sim

if TYPE_CHECKING:
    from xiaoyu.dialogue.context import StateTracker


class BaseIterator(AsyncIterator):
    """
    带状态的迭代器，用户序列化对话状态，以支持分布式部署。

    Attributes:
        node (BaseNode): 构造该迭代器的节点
        context (StateTracker): 对话上下文
        state (int): 迭代器的状态代码
        next_node (BaseNode): 下一个节点
        child (BaseIterator): 子迭代器
        end_flag (bool): 迭代器是否结束
    """

    START_STATE: int = 0

    def __init__(self, node: BaseNode, context: StateTracker):
        self.node: BaseNode = node
        self.context: StateTracker = context
        self.state: int = 0
        self.next_node: BaseNode = None
        self.child: BaseIterator = None
        self.end_flag: bool = False

    async def __anext__(self):
        await self.next()

    async def next(self) -> str:
        func = getattr(self, f"run_state_{self.state}", None)
        if func is None:
            raise ValueError(f"state {self.state} not found in {self.__class__.__name__}")
        obj = await func()
        if self.end_flag:
            raise StopAsyncIteration
        return obj

    def end(self) -> None:
        self.end_flag = True


class OptionIterator(BaseIterator):
    STATE_REPEATED: int = 1

    def __init__(self, node: BaseNode, context: StateTracker, repeat_times: int = 0):
        super().__init__(node, context)
        self._repeat_times: int = repeat_times

    async def run_state_0(self) -> str:
        msg: Message = self.context.latest_msg()
        if msg.text in self.node.option_child:
            option: str = msg.text
        else:
            # 根据编辑距离，算出与选项距离最小的候选项
            option_candidate, distance = levenshtein_sim(msg.text, list(self.option_child.keys()))
            # TODO 这里阈值写死，后续可以改成可配置的
            if distance / len(option_candidate) < 0.5:
                option = option_candidate
            else:
                option = msg.text

        option_node: BaseNode = self.node.option_child.get(option, None)

        if option_node:
            self.context.add_traceback_data(
                {
                    "line_id": self.node.line_id_mapping[option_node.node_name],
                    "conn_type": "option",
                    "type": "conn",
                    "source_node_name": self.node.node_name,
                    "target_node_name": option_node.node_name,
                    "option_name": msg.text,
                    "option_list": list(self.node.option_child.keys()),
                }
            )
            self.end()
            return option_node
        elif self._repeat_times <= 0 and self.context.trigger():
            # 触发其他对话流程意图成功，结束当前对话流程
            self.end()
        else:
            # 用户没有回答选项中的内容，走faq，FAQ若没有匹配到问题，则会走闲聊
            if "callback_words" in self.config:
                callback = random.choice(self.config["callback_words"])
            else:
                callback = "我没有理解您的意思，请您在选项中进行选择，或者接着询问其他问题。"
            msg.set_callback_words(callback)
            # 这里由于下一轮对话还是让用户进行选择，所以把选项参数返回给前端
            msg.options = self.config.get("options", [])
            self._repeat_times -= 1
            return FAQ_FLAG


class ForwardIterator(BaseIterator):
    def __init__(self, node: BaseNode, context: StateTracker, use_default: bool = True, life_cycle: int = 0):
        super().__init__(node, context)
        self._use_default: bool = use_default
        self._life_cycle: int = life_cycle

    async def run_state_0(self) -> str:
        msg = self.context.latest_msg()
        # 根据当前节点连接线配置的意图重新进行识别
        # 如果配置了内置意图，做一下识别
        for target_intent in self.node.intent_child:
            if target_intent in builtin_intent:
                intent = builtin_intent[target_intent].on_process_msg(msg)
            if target_intent in hard_code_intent:
                intent = hard_code_intent[target_intent].on_process_msg(msg)
        # TODO  这里是个坑，这里打下补丁。这里保存原始的intent，如果下一个触发节点为None，则流程结束，需要保存原来的intent
        origin_intent = msg.intent
        await msg.update_intent_by_candidate(self.intent_child)
        intent = msg.intent

        if intent in self.intent_child:
            next_node = self.intent_child[intent]
            self.context.add_traceback_data(
                {
                    "line_id": self.line_id_mapping[next_node.node_name],
                    "type": "conn",
                    "conn_type": "intent",
                    "source_node_name": self.node_name,
                    "target_node_name": next_node.node_name,
                    "intent_name": msg.get_intent_name_by_id(intent),
                    "match_type": "model",  # TODO 这里没有完成，需要做进一步判断
                    "match_words": "",  # TODO 这里没有完成，需要进一步做判断
                }
            )
            if not next_node:
                msg.intent = origin_intent
            self.end()
            self.next_node = next_node
        else:
            msg.understanding = "1"
            if self._use_default:  # 判断其他意图是否跳转
                next_node = self.default_child
                # 如果没有指定默认节点，并且只有一个意图子节点，则默认跳转到该意图子节点
                if not next_node and len(self.intent_child) == 1:
                    next_node = list(self.intent_child.values())[0]
                if not next_node:
                    msg.intent = origin_intent
                if (
                    self._life_cycle > 0 or not next_node or self.node.config.get("strict", False)
                ):  # 如果没有默认节点，则即使life_cycle用完也一直问
                    msg.set_callback_words(random.choice(self.node.config["callback_words"]))
                    self.state = 1
                    self._life_cycle -= 1
                    return FAQ_FLAG
                else:
                    self.context.add_traceback_data(
                        {
                            "line_id": self.node.line_id_mapping[next_node.node_name],
                            "type": "conn",
                            "conn_type": "default",
                            "source_node_name": self.node.node_name,
                            "target_node_name": next_node.node_name,
                        }
                    )
                    # 如果没有匹配到意图，跳转到默认分支节点，并强制将当前意图设置为默认意图
                    msg.intent = self.default_intent_id
                    self.end()
                    self.next_node = next_node


def simple_type_checker(key: str, dtype: type) -> Callable:
    def get_class_name(cls):
        return cls.__name__

    def check(node, value):
        if not isinstance(value, dtype):
            reason = "字段{}的值必须是类型{}，" "但是配置的类型是{}。".format(key, get_class_name(dtype), get_class_name(type(value)))
            raise DialogueStaticCheckException(key, reason, node.node_name)

    return check


def optional_value_checker(key: str, ref_values: List[str]) -> Callable:
    def check(node, value):
        if value not in ref_values:
            reason = "字段{}的值必须是{}中的值之一," " 而不是{}。".format(key, ref_values, value)
            raise DialogueStaticCheckException(key, reason, node.node_name)

    return check


def callback_cycle_checker() -> Callable:
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


def empty_checker() -> Callable:
    def check(*_):
        return None

    return check


class BaseNode(ABC):
    """对话流程节点基类

    Attributes:
        config (dict): 节点配置信息
        default_child (BaseNode): 默认连接的子节点
        intent_child (dict): key值为intent的id，value为子节点
        branch_child (dict): key值未分支的id，value为子节点
        option_child (dict): key值为选项字符串，value为子节点
        line_id_mapping (dict): key值为子节点的node_name，value为连线的id
        default_intent_id (str): 默认意图的id

    Nodes：
        判断子节点的优先级为intent_child > branch_child > default_child
    """

    # 节点类别的名称
    NODE_NAME: str = "基类节点"

    base_checkers: Dict[str, Callable] = dict(
        node_id=simple_type_checker("node_id", str),
        node_name=simple_type_checker("node_name", str),
        node_type=empty_checker(),
    )
    required_checkers: Dict[str, Callable] = {}
    optional_checkers: Dict[str, Callable] = {}

    # 此属性必须被子类复写
    traceback_template: Dict[str, Any] = {}

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_child: Optional[BaseNode] = None
        self.intent_child: Dict[str, BaseNode] = {}
        self.branch_child: Dict[str, BaseNode] = {}
        self.option_child: Dict[str, BaseNode] = {}

        self.line_id_mapping: Dict[str, str] = {}
        self.default_intent_id: str = ""

    @property
    def node_name(self) -> str:
        """
        获取用户定义的节点的名称, 注意与NODE_NAME的区别。
        """
        return self.config.get("node_name", "unknown")

    def __call__(self, context: StateTracker) -> AsyncIterator:
        traceback_data = deepcopy(self.traceback_template)
        traceback_data["node_name"] = self.node_name
        context.add_traceback_data(traceback_data)
        return self.call(context)

    @abstractmethod
    def call(self, context: StateTracker) -> AsyncIterator:
        raise NotImplementedError

    def static_check(self) -> None:
        """
        静态检查配置的数据结构
        """
        required_checkers = chain(self.base_checkers.items(), self.required_checkers.items())
        for key, func in required_checkers:
            if key in self.config:
                func(self, self.config[key])
            else:
                raise DialogueStaticCheckException(key, "该节点缺少此必填字段", self.node_name)

        for key, func in self.optional_checkers.items():
            if key in self.config:
                func(self, self.config[key])

        self.node_specific_check()

    def node_specific_check(self) -> None:
        """
        节点类型特定的检查
        """
        pass

    def add_child(
        self,
        node: BaseNode,
        line_id: str,
        branch_id: Optional[str] = None,
        intent_id: Optional[str] = None,
        option_id: Optional[str] = None,
        default: bool = False,
    ) -> None:
        """向当前节点添加子节点

        Args:
            node (BaseNode): 子节点
            branch_id (str, optional): 判断分支的id. Defaults to None.
            intent_id (str or list, optional): 意图分支的id. Defaults to None.
            option_id (str, optional): 用户选项分支的id. Default to None.
            default (bool, optional): 是否是默认子节点. Defaults to False.

        Nodes:
            branch_id，intent_id, option_id指定时三者只能选一
        """
        self.line_id_mapping[node.node_name] = line_id
        if option_id:
            self.option_child[option_id] = node
        elif branch_id:
            self.branch_child[branch_id] = node
        elif intent_id:
            # 这里意图跳转支持多个意图跳转到同一个下游节点
            if isinstance(intent_id, str):
                self.intent_child[intent_id] = node
            else:
                for intent_id_ in intent_id:
                    self.intent_child[intent_id_] = node
                    if intent_id_ == "0":  # “0”代表其他意图，没有训练数据与其对应
                        self.default_child = node

        else:
            # 如果该连接线没有指定选项、意图、分支，则认为是默认子节点
            self.default_child = node

        # 如果参数配置为默认子节点，则也将该节点设置为默认子节点
        if default:
            self.default_child = node

            # 这里如果是意图跳转，需要记录默认连接线对应的意图id，如果是非strict模式，则将意图设置为默认意图的id
            if intent_id:
                self.default_intent_id = intent_id

    def _eval(self, source: str, target: str, operator: str) -> bool:
        """
        判断source与target是否符合operator的条件

        Args:
            source (str): 运算符左侧的值
            target (str): 运算符右侧的值
            operator (str): 运算符

        Returns:
            bool: source 与 target 是否符合 operator 的条件
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

            # 字符串长度判断
            # TODO 这里需要检验类型
            if operator == "len_gt":
                return len(source) > int(target)
            if operator == "len_lt":
                return len(source) < int(target)
            if operator == "len_eq":
                return len(source) == int(target)

            return False

    def _judge_condition(self, context: StateTracker, condition: Dict) -> bool:
        msg = context.latest_msg()
        type = condition["type"]
        operator = condition["operator"]
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
                self.config["node_name"],
            )

    def _judge_branch(self, context: StateTracker, conditions: List):
        for condition in conditions:
            result = True
            for item in condition:
                result = result and self._judge_condition(context, item)
            if result:
                return True
        return False


class TriggerNode(BaseNode):
    def trigger(self):
        """
        判断该节点是否会被触发，子类必须复写该方法

        Return:
            bool: 触发为True，没有触发为False
        """
        raise NotImplementedError
