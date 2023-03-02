"""动态机器人说节点"""
from __future__ import annotations

import json
import random
import re
import warnings
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Union

from xiaoyu.dialogue.dynamic import (
    FIX_QUESTIONS,
    MAIN_QUESTION_PERSPECTIVE,
    ROBOT_CODE,
    ROBOT_CODE_INTENT,
    SUB_QUESTION_PERSPECTIVE,
)
from xiaoyu.dialogue.nodes.base import (
    BaseIterator,
    BaseNode,
    ForwardIterator,
    optional_value_checker,
    simple_type_checker,
)
from xiaoyu.rpc.search import intent_classify, search
from xiaoyu.utils.exceptions import DialogueStaticCheckException

if TYPE_CHECKING:
    from xiaoyu.dialogue.context import StateTracker


__all__ = ["DynamicNode"]


class DynamicNodeIterator(BaseIterator):
    def __init__(self, node: BaseNode, context: StateTracker):
        super().__init__(node, context)
        self.next_qid: Optional[Union[str, List[str]]] = None
        self.selected_intent_id: Optional[str] = None
        self.candidates: List[Dict[str, Any]] = []

    async def _forward_intent(self, data: Dict[str, Any]) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Returns:
            list: 子问题id列表
            str: 需要匹配的意图
        """
        intent_ids = data["intent_ids"]
        should_perspective = " ".join(intent_ids)
        response_data = search(
            robot_code=ROBOT_CODE_INTENT,
            question=FIX_QUESTIONS,
            should_perspective=should_perspective,
            recommend_num=-1,
            ans_threshold=100,  # 设置一个非常大的值，保证没有答案返回
            use_model=False,
            rcm_threshold=-100,  # 设置一个非常小的值，保证匹配到的都作为推荐问题
        )
        # 根据模式轮询提问
        msg = self.context.latest_msg()
        items = [json.loads(item) for item in response_data["recommendAnswers"]]

        selected = None
        # 规则识别意图
        for item in items:
            if "intent_rules" not in item or not item["intent_rules"]:
                continue
            for rule in item["intent_rules"]:
                # TODO 判断strict条件，增加命名实体的判断
                try:
                    if re.match(rule["regx"], msg.text):
                        selected = item
                        break
                except Exception:
                    warnings.warn("正则表达式匹配出错，规则：{}，问题：{}。intent_id: {}".format(rule["regx"], msg.text, item["intent_id"]))
                    continue
            if selected:
                break

        # 意图语义分类识别意图
        if not selected:
            response_data = intent_classify(
                question=msg.text,
                intent_group={item["intent_id"]: item["examples"] for item in items},
            )
            if len(response_data["topn_score"]) > 0:  # 防止没有匹配到任何意图
                tmp_selected = max(items, key=lambda item: max(response_data["topn_score"].get(item["intent_id"], [0])))
                if max(response_data["topn_score"][tmp_selected["intent_id"]]) >= 0.5:
                    selected = tmp_selected

        # TODO 目前只支持意图相关的识别能力
        # @sys.recent_intent @sys.recent_usersays
        for slot in data["slot"]:
            warning = slot.get("warning", False)
            if slot["entity_key"] == "@sys.recent_usersays":
                self.context.fill_slot(slot["key"], msg.text, slot["name"], warning)
            elif slot["entity_key"] == "@sys.recent_intent" and selected:
                self.context.fill_slot(slot["key"], selected["intent_name"], slot["name"], selected.get("warning", warning))
            elif slot["entity_key"] == "@sys.recent_intent_and_says" and selected:
                self.context.fill_slot(slot["key"], selected["intent_name"], slot["name"], selected.get("warning", warning))
            elif slot["entity_key"] == "@sys.recent_intent_and_says" and not selected:
                self.context.fill_slot(slot["key"], msg.text, slot["name"], warning)

        if selected and data["child_ids"] and data["intent_ids"]:
            selected_intent_id = selected["intent_id"]
            return data["child_ids"], selected_intent_id
        elif data["child_ids"]:
            return data["child_ids"], None
        else:
            return None, None

    async def run_state_0(self) -> Optional[str]:
        # 获取全局参数
        if "global_qestion_id" not in self.context.params:
            raise ValueError("调用动态机器人说节点时需指定global_qestion_id参数，通过该参数与问题库中问题的lib_ids参数匹配得到动态问题。")
        lib_id = str(self.context.params.get("global_qestion_id"))

        perspective = [lib_id]
        if self.next_qid:
            # 如果指定了next_qid则确认是子问题
            perspective.append(SUB_QUESTION_PERSPECTIVE)
        else:
            perspective.append(MAIN_QUESTION_PERSPECTIVE)

        # 从问题库中请求出问题
        random_mode = self.node.config.get("random_mode", 1)  # 1为指定问题，2为指定类别
        if self.next_qid:
            should_perspective = [self.next_qid] if isinstance(self.next_qid, str) else self.next_qid
        elif random_mode == 2:
            should_perspective = self.node.config.get("categories", [])
        else:  # random_mode == 1
            should_perspective = [self.node.config["qes_id"]]
        response_data = await search(
            robot_code=ROBOT_CODE,
            question=FIX_QUESTIONS,
            perspective=" ".join(perspective),
            should_perspective=" ".join(should_perspective),
            recommend_num=-1,
            ans_threshold=100,  # 设置一个非常大的值，保证没有答案返回
            use_model=False,
            rcm_threshold=-100,  # 设置一个非常小的值，保证匹配到的都作为推荐问题
        )
        if "recommendAnswers" not in response_data or not response_data["recommendAnswers"]:
            if random_mode == 2:
                raise ValueError(f"问题库{lib_id}中，没有匹配到指定类别{should_perspective}的问题。")
            else:
                raise ValueError(f"问题库{lib_id}中，没有匹配到指定id为{should_perspective}的问题。")
        # 根据模式轮询提问
        items = [json.loads(item) for item in response_data["recommendAnswers"]]
        if self.selected_intent_id:
            items = list(filter(lambda item: item.get("parent_intent_id") == self.selected_intent_id, items))
            if len(items) == 0:  # 对应意图没有触发任何子问题，则直接返回
                return await self.run_state_1()

        if self.node.config["random_mode"] == 1 or self.next_qid:
            self.candidates.append(items[0])
            self.state = 1
            return items[0]["content"]
        else:
            items = random.sample(items, k=self.node.config["choice"])
            self.candidates.extend(items[1:])
            self.state = 1
            return items[0]["content"]

    async def run_state_1(self) -> Optional[str]:
        if len(self.candidates) == 0:
            self.child = ForwardIterator(self.node, self.context)
            self.end()
            return
        qids, self.selected_intent_id = await self._forward_intent(self.context, self.candidates.pop())
        self.next_qid = qids
        return await self.run_state_0()


class DynamicNode(BaseNode):
    NODE_NAME = "动态机器人说节点"

    required_checkers: Dict[str, Callable] = OrderedDict(
        random_mode=optional_value_checker("random_node", [1, 2]),
    )

    optional_checkers: Dict[str, Callable] = OrderedDict(
        choice=simple_type_checker("choice", int),
        qes_id=simple_type_checker("qes_id", str),
        categories=simple_type_checker("categories", list),
        rule=optional_value_checker("rule", ["polling", "no_repeat"]),
    )

    traceback_template: Dict[str, Any] = {
        "type": "dynamic",
        "node_name": "",
        "robot_says": "",
        "user_says": "",
        "intent": "",
        "slots": "",
    }

    def node_specific_check(self) -> None:
        if self.config["random_mode"] == 2 and (not self.config.get("rule") or not self.config.get("choice")):
            raise DialogueStaticCheckException("random_mode为2时，rule和choice字段不能为空。")

        if self.config["random_mode"] == 1 and not self.config.get("qes_id"):
            raise DialogueStaticCheckException("qes_id", "random_mode为2时，qes_id不能为空", self.node_name)

    def call(
        self,
        context: StateTracker,
    ) -> DynamicNodeIterator:
        return DynamicNodeIterator(context, self)
