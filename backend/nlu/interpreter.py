import re
import json

from rasa_nlu.model import Interpreter

from .train import (get_model_path,
                    get_nlu_data_path,
                    create_lock,
                    release_lock,
                    get_using_model)
from utils.define import NLU_MODEL_USING


__all__ = ["Message", "get_interpreter", "load_all_using_interpreters"]


class Message(object):
    def __init__(
        self,
        raw_message
    ):
        self.intent = raw_message['intent']['name']
        self.entities = {i['entity']: i['value']
                         for i in raw_message['entities']}
        self.text = raw_message['text']
        self.regx = []
        self.key_words = []

    def get_intent(self):
        return self.intent

    def get_entities(self):
        return self.entities

    def __str__(self):

        string = """
            \nMessage Info:\n\tText: %s\n\tIntent: %s\n\tEntites:\n\t\t%s\n
        """ % (self.text, self.intent, self.entities)
        return string


class CustormInterpreter(object):
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
            if len(v.findall(text)) > 0:
                msg.regx.append(k)

        for k, v in self.key_words.items():
            for word in v:
                if word in text:
                    msg.key_words.append(k)
                    break
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
    interpreter = Interpreter.load(model_path)
    custom_interpreter = CustormInterpreter(robot_code, version, interpreter)
    cache[robot_code] = custom_interpreter
    return custom_interpreter


def get_interpreter(robot_code, version):
    """获取语义理解器，如果缓存中存在，则从缓存中加载，如果缓存中不存在则重新创建
       cache中的所有解释器模型所在的目录都会被NLU_MODEL_USING锁锁定

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 模型版本

    Returns:
        CustormInterpreter: 创建的CustormInterpreter对象
    """
    if robot_code in cache and cache[robot_code].version != version:
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
    程序首次启动时，将程序上次运行时正在使用的模型加载到缓存中
    """
    using_model_meta = get_using_model()
    for robot_code, version in using_model_meta:
        cache[robot_code] = create_interpreter(robot_code, version)
