"""语义理解单元，Interpreter."""
import json
import re
from collections import defaultdict
from typing import Dict

import dimsim
import ngram

from xiaoyu.nlu.train import (
    create_lock,
    get_nlu_data_path,
    get_using_model,
    release_lock,
)
from xiaoyu.rpc.faq import faq_ask, faq_chitchat_ask
from xiaoyu.rpc.search import intent_classify
from xiaoyu.utils.define import NLU_MODEL_USING, UNK, get_chitchat_faq_id

__all__ = [
    "Message",
    "get_interpreter",
    "load_all_using_interpreters",
    "Interpreter",
    "get_empty_interpreter",
]


class Message(object):
    """语义理解包装消息.

    Attributes:
        robot_code (str): 该消息关联的机器人id
        intent (str): 识别到的意图名称
        intent_confidence (float): 意图识别的置信概率值
        entities (dict): key为ner识别到的实体，key为实体类型（对应识别能力类型)
                         value为实体值，value是一个list表示可以识别到多个
        text (str): 用户回复的原始内容
        understanding (bool): 机器人是否理解当前会话，主要针对faq是否匹配到正确答案
        intent_id2name (dict): 意图id到意图名称的映射
        intent_id2examples (dict): 意图id到对应训练数据的映射
        intent_id2code (dict): 意图id到意图代码的映射
        callback_words (str): 机器人在运行过程中为当前会话设置拉回话术，使得用户回到正常的对话流程中。通常此callback_word会与闲聊或者faq进行拼接。
        chitchat_words (str): 闲聊接口的返回结果
        is_start (bool): 记录当前会话是否经过开始节点，用于前端进行统计
    """

    def __init__(
        self,
        raw_message,
        robot_code,
        intent_id2name={},
        intent_id2examples={},
        intent_id2code={},
    ):
        """初始化."""
        self.robot_code = robot_code
        # 处理raw_message中没有intent字段的情况
        if not raw_message["intent"]:
            self.intent_ranking = {UNK: 0}
        else:
            # 这里强制转换str类型是因为rasa的一个坑，某些情况下会返回 numpy._str类型，导致json无法序列化
            self.intent_ranking = {item["name"]: float(item["confidence"]) for item in raw_message["intent_ranking"]}

        self.entities = defaultdict(list)
        for item in raw_message["entities"]:
            self.entities[item["entity"]].append(item["value"])
        self.text = raw_message["text"]
        self.regx = defaultdict(list)
        self.key_words = defaultdict(list)
        self.faq_result = None
        self.options = []
        self.traceback_data = []
        self.intent_id2code = intent_id2code
        self.intent_id2name = intent_id2name
        self.intent_id2examples = intent_id2examples
        # 标识当前对话是否被理解，如果对话过程中没有被特别设置，该参数默认为True，0为己理解，1为未理解意图，2为未抽到词槽，3为匹配到faq知识库问题
        self.understanding = "0"
        self.callback_words = ""
        self.chitchat_words = ""
        self.is_start = False

    def set_callback_words(self, words):
        """设置对话拉回话术，默认为空字符串."""
        self.callback_words = words

    def get_intent_name_by_id(self, intent_id):
        """通过意图id获取意图名称，如果意图id与名称的映射不存在，则返回意图id的值."""
        return self.intent_id2name.get(intent_id, intent_id)

    def get_intent_code_by_id(self, intent_id):
        """通过意图id获取意图代号，如果意图id与意图代号的映射不存在，则返回意图id的值."""
        return self.intent_id2code.get(intent_id, intent_id)

    def add_intent_ranking(self, intent, confidence):
        self.intent_ranking.update({intent: confidence})

    def add_entities(self, key, value):
        """
        外部识别能力向msg添加抽取到的实体.

        Args:
            key(str): 实体类型名称
            value(list): 抽取到的实体值
        """
        if isinstance(value, str):
            value = [value]
        if key not in self.entities:
            self.entities[key] = []
        self.entities[key].extend(value)

    def update_intent(self):
        """根据当前intent_ranking 的内容更新当前intent."""
        if len(self.intent_ranking) == 0:
            self.intent = UNK
            self.intent_confidence = 0
        else:
            self.intent = max(self.intent_ranking.keys(), key=(lambda key: self.intent_ranking[key]))
            self.intent_confidence = self.intent_ranking[self.intent] / sum(self.intent_ranking.values())

    async def update_intent_by_candidate(self, candidates):
        """根据候选意图更新当前的意图状态.

        Args:
            candidates(list) : 候选意图，识别的意图只在候选意图中进行选择。如果指定candidate为None，则默认所有意图为候选
        """
        intent_group = {
            # 这里判断 intent 是否在 intent_id2example 中是防止给的候选意图中训练数据里没有
            intent: self.intent_id2examples[intent]
            for intent in candidates
            if intent in self.intent_id2examples
        }
        scores = await intent_classify(self.text, intent_group)

        # 这里取意图向量匹配的相似度值，和其他规则匹配相似度值的最大值
        intents_candidates = {intent: max(scores) for intent, scores in scores["data"]["topn_score"].items()}

        # 规则意图识别
        for intent in candidates:
            if intents_candidates.get(intent, 0) < self.intent_ranking.get(intent, 0):
                intents_candidates[intent] = self.intent_ranking.get(intent, 0)

        # 对于ASR的识别结果，或者错误输入的结果，这里对用户话术的发音进行相似度匹配
        for intent_id, examples in intent_group.items():
            for example in filter(lambda x: len(x) == len(self.text), examples):
                try:
                    if dimsim.get_distance(example, self.text) < 30 and len(self.text) >= 2:
                        # TODO 这里应该动态设置成识别到意图的阈值
                        intents_candidates[intent_id] = max(intents_candidates.get(intent_id, 0), 0.5)
                except Exception:
                    # 文字中存在英文或其他不是纯中文的符号，会出现这种情况
                    continue

        if len(intents_candidates) == 0:
            self.intent = UNK
            self.intent_confidence = 0
            return

        max_score = max(intents_candidates.values())

        if max_score >= 0.5:  # TODO 这里暂时写死阈值，后面改成可配置的变量
            self.intent = max(intents_candidates.keys(), key=(lambda key: intents_candidates[key]))
            self.intent_confidence = intents_candidates[self.intent] / sum(intents_candidates.values())
        else:
            self.intent = UNK
            self.intent_confidence = 0

    def get_abilities(self):
        """各个识别能力抽取到的实体集合，ner+regx+keywords.

        Returns:
            dict: key为识别能力名称，value为识别到的实体内容，value为list可以是多个
        """
        return self.entities

    def trigger_faq(self):
        """判断当前消息是否触发faq.

        Returns:
            bool: 如果为True，则触发faq，如果为false则不触发faq
        """
        # TODO 这里阈值可以写成配置
        return self.faq_result["confidence"] > 0.6

    async def perform_faq(self):
        """异步请求faq服务器，获取faq数据."""
        if not self.faq_result:
            self.faq_result = await faq_ask(self.robot_code, self.text)

        if self.get_faq_id() == UNK and not self.chitchat_words:
            self.chitchat_words = await self.perform_chitchat()

    def get_faq_answer(self):
        """
        获取faq的答案，一般在判断触发faq后调用此方法获得faq的答案.

        Returns:
            str: 匹配到的faq问题对应的答案
        """
        if self.faq_result is None or self.faq_result["faq_id"] == UNK:
            return (self.chitchat_words + "\n" + self.callback_words).strip()
        return (self.faq_result["answer"] + "\n" + self.callback_words).strip()

    def get_faq_id(self):
        """获取faq引擎匹配到的问题的id."""
        if self.faq_result is None:
            return UNK
        return self.faq_result["faq_id"]

    def __str__(self):
        """对象的字符串表示."""
        string = """
            \nMessage Info:\n\tText: %s\n\tIntent: %s\n\tEntites:\n\t\t %s
            \tFaq:\n\t\t %s
        """ % (
            self.text,
            self.intent,
            self.get_abilities().items(),
            self.faq_result,
        )
        return string

    ###############################################################################
    # 下面的方法是记录调试信息的一些方法
    def add_traceback_data(self, data):
        """向调试信息中增加一个节点信息."""
        self.traceback_data.append(data)

    def update_traceback_data(self, key, value):
        """记录节点运行过程中的追踪信息."""
        if key not in self.traceback_data[-1]:
            raise RuntimeError("节点类型 {} 的调试信息没有 {} 关键字".format(self.traceback_data[-1]["type"], key))

        if isinstance(self.traceback_data[-1][key], list):
            self.traceback_data[-1][key].append(value)
        else:
            self.traceback_data[-1][key] = value

    def get_latest_node_data(self):
        """获取最近一个节点信息."""
        if self.is_traceback_empty:
            return None
        else:
            return self.traceback_data[-1]

    @property
    def is_traceback_empty(self):
        """
        当前消息traceback数据是否为空
        """
        return len(self.traceback_data) == 0

    def get_xiaoyu_format_traceback_data(self):
        """
        将追踪的调试信息转换成小语后台需要的格式
        """
        xiaoyu_format_data = []
        for item in self.traceback_data:
            xiaoyu_format_data.append({"type": item["type"], "info": json.dumps(item, ensure_ascii=False)})
        return xiaoyu_format_data

    modal_words = "哪罢吧么嘛啊了啦吗呢呀哇"

    @property
    def text_without_modal(self):
        return re.sub(self.modal_words, "", self.text)

    ###############################################################################
    # 下面是nlu语义理解接口，将msg信息直接解析为字典格式，格式示例如下
    # {
    #     "intent": "car_number",
    #     "intent_confidence": "0.9",
    #     "entities": {
    #         "plate_number": ["粤A23456"]
    #     },
    #     "sentiment": 0.6
    # }
    def to_dict(self):
        return {
            "intent": self.get_intent_code_by_id(self.intent),
            "remark": self.get_intent_name_by_id(self.intent),
            "intent_confidence": self.intent_confidence,
            "entities": self.entities
            # TODO sentiment here
        }

    ###############################################################################

    ###############################################################################
    # 调用闲聊相关接口
    async def perform_chitchat(self):
        """
        返回闲聊回答.

        Returns:
            str: 闲聊回答字符串
        """
        if CHITCHAT_SERVER_ADDR:
            return await async_post_rpc(
                f"http://{CHITCHAT_SERVER_ADDR}/xiaoyu/chitchat?text={self.text}",
                return_type="text",
            )
        else:
            return await faq_chitchat_ask(get_chitchat_faq_id(self.robot_code), self.text)

    ###############################################################################


class Interpreter(object):
    """语义理解器

    Attributes:
        interpreter (rasa_nlu.model.Interpreter): rasa原生的nlu语义理解器
        version (str): nlu模型的版本
        robot_code (str): 模型所属机器人的id
        intent (str): 意图和其对应的训练数据
        intent_matcher (str): 基于ngram的意图匹配器
        regx (dict): key为识别能力名称，value为对应的正则表达式
        key_words (dict): key为识别能力的名称，value为list，list中的每个元素为关键词
        intent_rules (list): 识别意图的正则表达式
    """

    def __init__(self, robot_code, version, raw_training_data):
        self.version = version
        self.robot_code = robot_code
        regx = raw_training_data["regex_features"]
        examples = raw_training_data["rasa_nlu_data"]["common_examples"]
        intent = {}
        for example in examples:
            if example["intent"] not in intent:
                intent[example["intent"]] = [example["text"]]
            else:
                intent[example["intent"]].append(example["text"])
        self.intent = intent
        self.intent_matcher = {
            intent_id: ngram.NGram(examples, N=2, threshold=0.2) for intent_id, examples in self.intent.items()
        }

        self.regx = {key: [re.compile(item) for item in value] for key, value in regx.items()}
        self.key_words = raw_training_data["key_words"]
        self.intent_rules = raw_training_data["intent_rules"]
        # 如果训练数据中字符数大于等于二，也将其直接加入到规则匹配
        for example in examples:
            if len(example["text"]) < 2:
                continue
            item = {
                "regx": re.escape(example["text"]),
                "strict": False,
            }
            if example["intent"] not in self.intent_rules:
                self.intent_rules[example["intent"]] = [item]
            else:
                self.intent_rules[example["intent"]].append(item)

        self.intent_id2name = raw_training_data.get("intent_id2name", {})
        self.intent_id2code = raw_training_data.get("intent_id2code", {})

    def get_examples_by_intent(self, intent_id):
        """
        根据意图id获取对应的训练数据
        """
        return self.intent[intent_id]

    def get_empty_msg(self, text=""):
        """
        获取一个空的消息对象，用于对话开始时没有消息进行解析的情况
        """
        raw_msg = {"text": text, "intent": "", "entities": {}}
        return Message(
            raw_msg,
            self.robot_code,
            intent_id2name=self.intent_id2name,
            intent_id2examples=self.intent,
            intent_id2code=self.intent_id2code,
        )

    async def parse(self, text, use_model=False, parse_internal_ner=False):
        """
        多轮对话语义解析

        Args:
            use_model (bool): 是否使用transformer模型匹配意图，如果为False则使用ngram匹配
            parse_internal_ner (bool): 是否对内置命名实体进行识别，如果为False则不进行识别

        Note:
            通常多轮对话过程中，这两个参数都设置为False，在对话流程控制中，会进行响应的匹配解析。
            如果是纯语义理解接口，则都设置为True
        """
        msg = self.get_empty_msg(text)
        # ngram解析意图
        intent_ranking = {}
        for intent_id, matcher in self.intent_matcher.items():
            match_result = matcher.search(text)
            if match_result:
                confidence = 0
                for item in sorted(match_result, key=lambda x: -x[1]):
                    confidence += (1 - confidence) * item[1]
                intent_ranking[intent_id] = confidence

        msg.intent_ranking = intent_ranking

        if use_model:
            await msg.update_intent_by_candidate(self.intent_matcher.keys())

        # 解析意图规则
        for intent_id, rules in self.intent_rules.items():
            for rule in rules:
                try:
                    match_result = re.search(rule["regx"], text)
                except Exception:
                    raise RuntimeError("意图{}正则表达式{}不合法，请检查意图训练数据。".format(intent_id, rule["regx"]))
                if match_result:
                    msg.add_intent_ranking(intent_id, 1)
                    break
        msg.update_intent()

        # ner
        # 正则解析ner
        for k, vs in self.regx.items():
            for v in vs:
                regx_values = v.findall(text)
                if len(regx_values) > 0:
                    msg.add_entities(k, regx_values)

        # 同义词解析ner
        for k, v in self.key_words.items():
            words = list(filter(lambda x: x in msg.text, v))
            if len(words) > 0:
                msg.add_entities(k, words)

        # 解析系统内置实体
        if parse_internal_ner:
            for builtin_ne in ne_extract_funcs:
                for item in builtin_ne(msg):
                    pass
        return msg


def get_interpreter(model_storage_folder, robot_code, version):
    """创建一个新的语义理解器

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 模型版本

    Returns:
        Interpreter: 创建的CustormInterpreter对象
    """
    release_lock(model_storage_folder, robot_code, status=NLU_MODEL_USING)
    create_lock(model_storage_folder, robot_code, version, NLU_MODEL_USING)
    nlu_data_path = get_nlu_data_path(model_storage_folder, robot_code, version)
    with open(nlu_data_path, "r", encoding="utf-8") as f:
        raw_training_data = json.load(f)
    custom_interpreter = Interpreter(robot_code, version, raw_training_data)
    return custom_interpreter


def get_empty_interpreter(robot_code):
    # TODO
    raw_training_data = {
        "rasa_nlu_data": {
            "common_examples": [
                {"text": "确认", "intent": "__1"},
                {"text": "ok", "intent": "__1"},
                {"text": "好的", "intent": "__1"},
                {"text": "不行", "intent": "__2"},
                {"text": "不可以", "intent": "__2"},
                {"text": "No", "intent": "__2"},
            ]
        },
        "regex_features": {},
        "key_words": {},
        "intent_rules": {},
        "intent_id2name": {},
    }

    return Interpreter(robot_code, "empty", raw_training_data)


def load_all_using_interpreters(model_storage_folder: str) -> Dict[str, Interpreter]:
    """
    程序首次启动时，将程序上次运行时正在使用的模型加载到缓存中，并返回机器人id和其对应的版本
    """
    cache = {}
    using_model_meta = get_using_model(model_storage_folder)
    for robot_code, version in using_model_meta.items():
        cache[robot_code] = get_interpreter(model_storage_folder, robot_code, version)
    return cache
