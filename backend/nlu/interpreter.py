import re
import json

from collections import defaultdict
from itertools import chain
from rasa_nlu.model import Interpreter

from backend.nlu.train import (get_model_path,
                               get_nlu_data_path,
                               create_lock,
                               release_lock,
                               get_using_model)
from backend.faq import faq_ask
from utils.define import NLU_MODEL_USING
from utils.exceptions import NoAvaliableModelException


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
    """

    def __init__(
        self,
        raw_message
    ):
        self.intent = raw_message['intent']['name']
        self.intent_confidence = raw_message['intent']['confidence']
        self.entities = defaultdict(list)
        for item in raw_message['entities']:
            self.entities[item["entity"]].append(item["value"])
        self.text = raw_message['text']
        self.regx = defaultdict(list)
        self.key_words = defaultdict(list)
        self.faq_result = None

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

    def __str__(self):

        string = """
            \nMessage Info:\n\tText: %s\n\tIntent: %s\n\tEntites:\n\t\t %s
            \tFaq:\n\t\t %s
        """ % (self.text, self.intent, self.get_abilities(), self.faq_result)
        return string


class CustormInterpreter(object):
    """语义理解器

    Attributes:
        interpreter (rasa_nlu.model.Interpreter): rasa原生的nlu语义理解器
        version (str): nlu模型的版本
        robot_code (str): 模型所属机器人的id
        regx (dict): key为识别能力名称，value为对应的正则表达式
        regx (dict): key为识别能力的名称，value为list，list中的每个元素为关键词
    """

    def __init__(self, robot_code, version, interpreter):
        self.interpreter = interpreter
        self.version = version
        self.robot_code = robot_code
        nlu_data_path = get_nlu_data_path(robot_code, version)
        with open(nlu_data_path, "r") as f:
            raw_training_data = json.load(f)
        regx = raw_training_data['rasa_nlu_data']['regex_features']
        self.regx = {item['name']: re.compile(
            item['pattern']) for item in regx}
        key_words = raw_training_data['rasa_nlu_data']['key_words']
        self.key_words = {item['name']: item['synonyms'] for item in key_words}

    def parse(self, text):
        raw_msg = self.interpreter.parse(text)
        msg = Message(raw_msg)
        for k, v in self.regx.items():
            regx_values = v.findall(text)
            if len(regx_values) > 0:
                msg.regx[k] = regx_values

        for k, v in self.key_words.items():
            for word in v:
                if word in text:
                    msg.key_words[k].append(word)
        msg.faq_result = faq_ask(self.robot_code, text, raw=True)
        return msg


cache = dict()


def create_interpreter(robot_code, version):
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
            "获取模型错误，请检查机器人{}是否存在版本{}。".format(robot_code, version))
    custom_interpreter = CustormInterpreter(robot_code, version, interpreter)
    cache[robot_code] = custom_interpreter
    return custom_interpreter


def get_interpreter(robot_code, version=None):
    """获取语义理解器，如果缓存中存在，则从缓存中加载，如果缓存中不存在则重新创建
       cache中的所有解释器模型所在的目录都会被NLU_MODEL_USING锁锁定

    Args:
        robot_code (str): 机器人唯一标识
        version (str, optional): 模型版本。Default is None. 如果该参数为None，直接加载缓存中的模型。

    Returns:
        CustormInterpreter: 创建的CustormInterpreter对象
    """
    if version is None and robot_code in cache:
        return cache[robot_code]
    elif version is None and robot_code not in cache:
        raise NoAvaliableModelException(
            "获取模型错误，请检查机器人{}是否有可用的语义理解模型。".format(robot_code))

    elif robot_code in cache and cache[robot_code].version == version:
        return cache[robot_code]

    elif robot_code in cache and cache[robot_code].version != version:
        release_lock(robot_code, cache[robot_code].version)
        create_lock(robot_code, version, NLU_MODEL_USING)
        cache[robot_code] = create_interpreter(robot_code, version)
        return cache[robot_code]
    else:
        create_lock(robot_code, version, NLU_MODEL_USING)
        cache[robot_code] = create_interpreter(robot_code, version)
        return cache[robot_code]


def load_all_using_interpreters():
    """
    程序首次启动时，将程序上次运行时正在使用的模型加载到缓存中，并返回机器人id和其对应的版本
    """
    using_model_meta = get_using_model()
    for robot_code, version in using_model_meta:
        cache[robot_code] = create_interpreter(robot_code, version)
    return using_model_meta
