import re
import json

from collections import defaultdict
from itertools import chain
from rasa_nlu.model import Interpreter

import backend.nlu.ability as ability
from backend.nlu.train import (get_model_path,
                               get_nlu_data_path,
                               release_lock,
                               create_lock,
                               get_using_model)
from backend.faq import faq_ask
from utils.exceptions import NoAvaliableModelException
from utils.define import (NLU_MODEL_USING,
                          MODEL_TYPE_NLU,
                          FAQ_UNKNOWN)


__all__ = ["Message", "get_interpreter", "load_all_using_interpreters"]


class Message(object):
    """语义理解包装消息

    Attributes:
        intent (str): 识别到的意图名称
        intent_confidence (float): 意图识别的置信概率值
        entities (dict): key为ner识别到的实体，key为实体类型（对应识别能力类型)
                         value为实体值，value是一个list表示可以识别到多个
        text (str): 用户回复的原始内容
        regx (dict): 正则识别能力，key为正则表达式识别到的实体，value为实体的值，value是一个list代表可能识别到多个
        key_words (dict): 关键词识别能力，key为关键词识别到的实体
                          value为识别到实体的值，value是一个list代表可能识别到多个
        understanding (bool): 机器人是否理解当前会话，主要针对faq是否匹配到正确答案
    """

    def __init__(
        self,
        raw_message
    ):
        # 处理raw_message中没有intent字段的情况
        if not raw_message["intent"]:
            self.intent = "unkonwn"
            self.intent_confidence = 0
        else:
            self.intent = raw_message['intent']['name']
            self.intent_confidence = raw_message['intent']['confidence']
        self.entities = defaultdict(list)
        for item in raw_message['entities']:
            self.entities[item["entity"]].append(item["value"])
        self.text = raw_message['text']
        self.regx = defaultdict(list)
        self.key_words = defaultdict(list)
        self.faq_result = None

    @property
    def understanding(self):
        return self.intent_confidence >= 0.5

    def get_intent(self):
        """获取用户的意图

        Returns:
            str: 用户意图名称
        """
        return self.intent

    def get_abilities(self):
        """各个识别能力抽取到的实体集合，ner+regx+keywords

        Returns:
            dict: key为识别能力名称，value为识别到的实体内容，value为list可以是多个
        """
        result = defaultdict(list)
        for ability, value in chain(self.entities.items(),
                                    self.regx.items(), self.key_words.items()):
            result[ability].extend(value)

        return result

    def trigger_faq(self):
        """判断当前消息是否触发faq

        Returns:
            bool: 如果为True，则触发faq，如果为false则不触发faq
        """
        # TODO 这里阈值可以写成配置
        return self.faq_result["confidence"] > 0.6

    def get_faq_answer(self):
        """
        获取faq的答案，一般在判断触发faq后调用此方法获得faq的答案

        Returns:
            str: 匹配到的faq问题对应的答案
        """
        return self.faq_result["answer"]

    def get_faq_id(self):
        """
        获取faq引擎匹配到的问题的id
        """
        return self.faq_result["faq_id"]

    def __str__(self):

        string = """
            \nMessage Info:\n\tText: %s\n\tIntent: %s\n\tEntites:\n\t\t %s
            \tFaq:\n\t\t %s
        """ % (self.text, self.intent, self.get_abilities().items(), self.faq_result)
        return string


class CustormInterpreter(object):
    """语义理解器

    Attributes:
        interpreter (rasa_nlu.model.Interpreter): rasa原生的nlu语义理解器
        version (str): nlu模型的版本
        robot_code (str): 模型所属机器人的id
        regx (dict): key为识别能力名称，value为对应的正则表达式
        key_words (dict): key为识别能力的名称，value为list，list中的每个元素为关键词
        internal_abilities (list): 内置识别能力的列表
        intent_rules (list): 识别意图的正则表达式
    """

    def __init__(self, robot_code, version, interpreter):
        self.interpreter = interpreter
        self.version = version
        self.robot_code = robot_code
        nlu_data_path = get_nlu_data_path(robot_code, version)
        with open(nlu_data_path, "r") as f:
            raw_training_data = json.load(f)
        regx = raw_training_data['regex_features']
        self.regx = {key: [re.compile(item) for item in value]
                     for key, value in regx.items()}
        self.key_words = raw_training_data['key_words']
        self.intent_rules = raw_training_data['intent_rules']
        self.internal_abilities = []

    def parse(self, text):
        raw_msg = self.interpreter.parse(text)
        msg = Message(raw_msg)
        # 解析意图规则
        for intent_id, rules in self.intent_rules.items():
            flag = False
            for rule in rules:
                if re.match(rule["regx"], text):
                    msg.intent = intent_id
                    msg.intent_confidence = 1
                    flag = True
            if flag:
                break

        # 解析自定义正则
        for k, vs in self.regx.items():
            values = []
            for v in vs:
                regx_values = v.findall(text)
                values.extend(regx_values)
            if len(values) > 0:
                msg.regx[k] = values
        # 解析内置能力正则
        for k, vs in ability.internal_regx_ability.items():
            if k not in self.internal_abilities:
                continue
            values = []
            for v in vs:
                regx_values = v.findall(text)
                values.extend(regx_values)
            if len(values) > 0:
                msg.regx[k] = values

        # 解析自定义同义词
        for k, v in self.key_words.items():
            for word in v:
                if word in text:
                    msg.key_words[k].append(word)
        msg.faq_result = faq_ask(self.robot_code, text)

        # 解析自定义ner识别能力
        entities = ability.ner(text)
        for key, value in entities.items():
            if key not in self.internal_abilities:
                continue
            msg.entities[key].extend(value)

        return msg

    def load_extra_abilities(self, names):
        """加载内置的识别能力

        Args:
            names (list): 识别能力的名称列表
        """
        self.internal_abilities = names


def get_interpreter(robot_code, version):
    """创建一个新的语义理解器

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 模型版本

    Returns:
        CustormInterpreter: 创建的CustormInterpreter对象
    """
    model_path = get_model_path(robot_code, version)
    try:
        interpreter = Interpreter.load(model_path)
    except Exception:
        raise NoAvaliableModelException(
            "获取模型错误，请检查机器人{}是否存在版本{}。".format(robot_code, version), version, MODEL_TYPE_NLU)
    # 被获取的模型会被标注为正在使用的模型
    release_lock(robot_code, status=NLU_MODEL_USING)
    create_lock(robot_code, version, NLU_MODEL_USING)
    custom_interpreter = CustormInterpreter(robot_code, version, interpreter)
    return custom_interpreter


def load_all_using_interpreters():
    """
    程序首次启动时，将程序上次运行时正在使用的模型加载到缓存中，并返回机器人id和其对应的版本
    """
    cache = {}
    using_model_meta = get_using_model()
    for robot_code, version in using_model_meta.items():
        cache[robot_code] = get_interpreter(robot_code, version)
    return cache
