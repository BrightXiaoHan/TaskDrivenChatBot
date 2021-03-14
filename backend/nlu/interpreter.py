import os
import json
from rasa_nlu.model import Interpreter

cwd = os.path.abspath(os.path.dirname(__file__))

__all__ = ["Message", "CustormInterpreter"]


def change_dir(func):

    def wrapper(*args, **kwargs):
        origin_dir = os.path.abspath(".")
        os.chdir(cwd)
        ret = func(*args, **kwargs)
        os.chdir(origin_dir)
        return ret

    return wrapper


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
    def __init__(self, robot_code, interpreter):
        self.interpreter = interpreter
        self.robot_code = robot_code
        nlu_data_path = os.path.join(cwd, "dataset", robot_code, "config.json")
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


@change_dir
def get_interpreter(robot_code):
    model_path = os.path.join(cwd, 'models', robot_code, 'default')
    interpreter = Interpreter.load(model_path)
    custom_interpreter = CustormInterpreter(robot_code, interpreter)
    return custom_interpreter
