import re
import time
import json

from collections import OrderedDict

import backend.dialogue.nodes as nodes
from utils.funcs import get_time_stamp, generate_uuid
from utils.exceptions import DialogueRuntimeException


FAQ_FLAG = "flag_faq"  # 标识当前返回的为faq

class StateTracker(object):
    """
    对话状态上下文追踪器

    Attributes:
        agent (dict): 会话管理单元
        graph (dict): 对话流程配置
        robot_code (str): 机器人唯一标识
        slots (dict): 需要填充的全局槽位
        slots_abilities (dict): 每个全局槽位对应的识别能力
        params (dict): 全局参数，流程配置中的global_params字段
        user_id (str): 会话的唯一标识
        state_recorder (list): 记录经过的每个节点的名称
        msg_recorder (list): 每个元素是一个backend.nlu.Message对象，记录每轮对话用户的回复，和nlu理解信息。
        response_recorder (list): 每个元素记录机器人每一轮对话的回复内容
        start_time (str): 对话开始时间，为float格式，直接由time.time()得到
        turn_id (int): 当前对话轮数记录
        slot_setting_turns (dict): 槽位填充对应的对话轮数，key为槽位名称，value为轮数
        time_stamp_turns (list): 记录每一轮对话的时间，每个元素的格式为(开始时间，结束时间)
                                格式与start_time字段相同，列表元素个数与总的对话轮数相同。

    """

    def __init__(
        self,
        agent,
        user_id,
        params
    ):
        self.agent = agent
        self.robot_code = self.agent.robot_code
        self.slots = {
            slot_name: None for slot_name in self.agent.slots_abilities}
        self.params = params
        self.user_id = user_id
        self.current_state = None
        self.state_recorder = list()
        self.msg_recorder = list()
        self.response_recorder = list()
        self.start_time = time.time()
        self.turn_id = 0
        self.entity_setting_turns = {}
        self.time_stamp_turns = []
        self.is_end = False

    def fill_slot(self, name, value):
        """
        全局槽位填充

        Args:
            name (str): 槽位名称
            value (str): 槽位对应的值
        """
        self.slots[name] = value
        # 记录槽位填充对应的对话轮数
        self.entity_setting_turns[name] = self.turn_id

    def establish_connection(self):
        for _, graph in self.agent.robot_ledding_graphs.items():
            node = graph[0]
            if node.trigger(self):
                self.current_state = node(self)
                return next(self.current_state)

        return "你好我是小语机器人，请问你有什么问题。"

    def switch_graph(self, graph_id, node_name):
        graph = self.agent.graphs.get(graph_id, None)
        if not graph:
            raise DialogueRuntimeException("切换流程图失败",
                                           self.robot_code, node_name)
        if isinstance(graph[0], nodes.SayNode):
            self.current_state = graph[0](self)
        else:
            self.current_state = None

    def handle_message(self, msg):
        """
        给定nlu模型给出的语义理解消息，处理消息记录上下文，并返回回复用户的话术
        Args:
            msg (backend.nlu.Message): 消息对象

        Return:
            str: 回复用户的话术
        """
        # 小语平台：记录起始时间
        start_time = get_time_stamp()

        # 记录消息
        self.msg_recorder.append(msg)

        def run():
            if self.current_state is None:
                for _, graph in self.agent.user_ledding_graphs.items():
                    node = graph[0]
                    if node.trigger(self):
                        self.current_state = node(self)
                        self.state_recorder.append(node.NODE_NAME)
                        break
            if self.current_state is None:
                response = msg.get_faq_answer()
                self.state_recorder.append("faq")
                # 记录机器人返回的话术
                self.response_recorder.append(FAQ_FLAG)
            else:
                while True:
                    response = next(self.current_state)
                    if isinstance(response, str):

                        # 记录机器人返回的话术
                        self.response_recorder.append(response)
                        break
                    elif response is not None:
                        # 记录节点名称
                        self.state_recorder.append(response.NODE_NAME)
                        self.current_state = response(self)
                    else:
                        self.current_state = None
                        break
            return response

        response = run()
        if not response:
            response = run()

        # 小语平台执行轮数加一
        self.turn_id += 1

        # 记录小语平台时间
        end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.time_stamp_turns.append((start_time, end_time))
        return self.response_recorder[-1]

    def _latest_msg(self):
        if len(self.msg_recorder) == 0:
            return None
        return self.msg_recorder[-1]

    def _get_empty_slot(self):
        empty_slots = list(
            filter(lambda x: self.entities[x] is None, self.entities))
        return empty_slots

    def get_ability_by_slot(self, slot_name):
        return self.agent.slots_abilities[slot_name]

    def decode_ask_words(self, content):
        """解析机器人说的内容，格式为${slot.全局槽位名}，${params.全局参数名}

        Args:
            content (str): 原始待参数引用的文本内容

        Return:
            str: 解析参数后的引用内容
        """
        def slot_replace_function(term):
            return self.slots.get(term.group(1), "unkown")

        def params_replace_function(term):
            return self.params.get(term.group(1), "unkown")

        content = re.sub(r"\$\{slot\.(.*?)\}", slot_replace_function, content)
        content = re.sub(r"\$\{params\.(.*?)\}",
                         slot_replace_function, content)
        return content

    def get_latest_xiaoyu_pack(self):
        """
        获取小语对话工厂最近一次的对话数据
        """
        dialog = {
            "code": generate_uuid(),
            "nodeId": self.state_recorder[-1],
            "is_end": self.is_end
        }
        if self.response_recorder[-1] == FAQ_FLAG:
            faq_answer_meta = self._latest_msg().get_faq_answer()
            try:
                faq_answer_meta = json.loads(faq_answer_meta)
            except:
                return {
                "sessionId": self.user_id,
                "says": faq_answer_meta,
                    "responseTime": get_time_stamp(),
                    "dialog": dialog,
                    "recommendQuestions": [],
                    "relatedQuest": [],
                    "hotQuestions": []
                }
            return {
                "sessionId": self.user_id,
                "says": faq_answer_meta["answer"],
                "responseTime": get_time_stamp(),
                "dialog": dialog,
                "recommendQuestions": faq_answer_meta["related_questions"],
                "relatedQuest": faq_answer_meta["similar_questions"],
                "hotQuestions": []
            }
        else:
            intent = {
                "understanding": self._latest_msg().understanding,  # 1是已经理解，2是未理解
                "intent": self._latest_msg().intent,
                "candidateIntent": []
            }
            entities = [{
                "key": key,
                "name": key,
                "value": value
            } for key, value in self._latest_msg().get_abilities().items()]
            slots = entities
            return {
                "sessionId": self.user_id,
                "says": self.response_recorder[-1],
                "responseTime": get_time_stamp(),
                "dialog": dialog,
                # 第一个请求为建立连接的请求，这些字段都应为空·
                "intent": intent if len(self.msg_recorder) > 1 else "",
                "slots": slots if len(self.msg_recorder) > 1 else [],
                "entities": entities if len(self.msg_recorder) > 1 else []
            }
