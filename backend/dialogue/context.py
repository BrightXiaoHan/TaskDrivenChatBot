import re
import time

from itertools import chain
from collections import OrderedDict

from utils.funcs import get_time_stamp


class StateTracker(object):
    """
    对话状态上下文追踪器

    Attributes:
        graph (dict): 对话流程配置
        robot_code (str): 机器人唯一标识
        slots (dict): 需要填充的全局槽位
        slots_abilities (dict): 每个全局槽位对应的识别能力
        params (dict): 全局参数，流程配置中的global_params字段
        user_id (str): 会话的唯一标识
        state_recorder (list): 记录经过的每个节点的名称
        msg_recorder (list): 每个元素是一个backend.nlu.Message对象，记录每轮对话用户的回复，和nlu理解信息。
        response_recorder (list): 每个元素记录机器人每一轮对话的回复内容
        start_time (str): 对话开始时间，记录格式为'%Y-%m-%d %H:%M:%S'
        turn_id (int): 当前对话轮数记录
        slot_setting_turns (dict): 槽位填充对应的对话轮数，key为槽位名称，value为轮数
        time_stamp_turns (list): 记录每一轮对话的时间，每个元素的格式为(开始时间，结束时间)
                                格式与start_time字段相同，列表元素个数与总的对话轮数相同。

    """

    def __init__(
        self,
        user_id,
        robot_code,
        graph,
        slots_abilities,
        params
    ):
        self.graph = graph
        self.robot_code = robot_code
        self.slots = {key: None for key in slots_abilities}
        self.slots_abilities = slots_abilities
        self.params = params
        self.user_id = user_id
        self.current_state = None
        self.state_recorder = list()
        self.msg_recorder = list()
        self.response_recorder = list()
        self.startTime = get_time_stamp()
        self.turn_id = 0
        self.entity_setting_turns = {}
        self.time_stamp_turns = []

    def fill_slot(self, name, value):
        """
        全局槽位填充

        Args:
            name (str): 槽位名称
            value (str): 槽位对应的值
        """
        self.entities[name] = value
        # 记录槽位填充对应的对话轮数
        self.entity_setting_turns[name] = self.turn_id

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

        response, self.current_state = self.current_state(self)
        # 记录节点名称
        self.state_recorder.append(self.current_state.__class__.__name__)

        # 记录机器人返回的话术
        self.response_recorder.append(response)

        # 小语平台执行轮数加一
        self.turn_id += 1

        # 记录小语平台时间
        end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.time_stamp_turns.append((start_time, end_time))
        return response

    def _latest_msg(self):
        return self.msg_recorder[-1]

    def _get_empty_slot(self):
        empty_slots = list(
            filter(lambda x: self.entities[x] is None, self.entities))
        return empty_slots

    def _get_logger_dict(self):
        result = dict()
        result['entities'] = self.entities

        states = list()
        # states = [msg.__class__.__name__ for msg in self.msg_recorder]
        for state_class_name, msg, response, time_stamp in zip(
                self.state_recorder, self.msg_recorder,
                self.response_recorder, self.time_stamp_turns):
            states.append(OrderedDict(
                user_response=msg.text,
                user_intent=msg.intent,
                entities=msg.entities,
                bot_response=response,
                intent_ranking=msg.intent_ranking,
                node_id=state_class_name,
                time_stamp=time_stamp
            ))
        result['state_tracker'] = states

        return result

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

    def get_logger(self):
        """
        获得会话日志，调试或者记录日志用
        Return:
            str: 会话日志内容
        """
        log_dict = self._get_logger_dict()
        str_builder = ""

        str_builder += "Entities:\n"
        for k, v in log_dict['entities'].items():
            str_builder += '\t%s: %s\n' % (k, v)

        str_builder += "\n\nStateTracker:\n\n"
        for i, item in enumerate(log_dict['state_tracker']):
            str_builder += "Round %d: \n" % i
            str_builder += "User_Response: %s. \n" % item.get('user_response')
            str_builder += "User_Intent: %s. \n" % item.get('user_intent')
            str_builder += "Entities: \n"
            for k, v in item.get('entities').items():
                str_builder += '\t%s: %s.\n' % (k, v)
            str_builder += "Bot_Response: %s. \n" % item.get('bot_response')
            str_builder += '\n'

        return str_builder

    def hang_up(self):
        self.current_state.hang_up(self)

    def get_latest_xiaoyu_pack(self):
        """
        获取小语对话工厂最近一次的对话数据
        """
        dialog = {
            "code": "user_{}".format(len(self.time_stamp_turns)),
            "nodeId": self.state_recorder[-1],
            "is_end": self.get_status_code() == 1
        }
        intent = {
            "understanding": self._latest_msg().understanding,  # 1是已经理解，2是未理解
            "intent": self._latest_msg().intent,
            "candidateIntent": []
        }
        entities = [{
            "key": key,
            "name": self.entity_name_mapping[key],
            "value": value
        } for key, value in self._latest_msg().entities.items()]
        slots = entities
        return {
            "dialog": dialog,
            # 第一个请求为建立连接的请求，这些字段都应为空·
            "intent": intent if len(self.msg_recorder) > 1 else "",
            "slots": slots if len(self.msg_recorder) > 1 else [],
            "entities": entities if len(self.msg_recorder) > 1 else []
        }

    def get_xiaoyu_pack(self):
        globalSlots = [
            {
                "code": self.entity_setting_turns.get(key, None),
                "name": self.entity_name_mapping.get(key, None),
                "key": key,
                "value": value
            } for key, value in self.entities.items()
        ]
        details = [[
            {
                "code": "user_{}".format(str(i)),
                "nodeId": tracker["node_id"],
                "type": "2",  # 1、一问一答/2、多轮对话/3、闲聊
                "speaker": "1",  # 1 为用户，2为机器人
                "time": tracker["time_stamp"][0],
                "context": tracker["user_response"],
                "understanding": "1-己理解/2-未理解",
                "intent": tracker["user_intent"],
                "candidateIntent": "候选意图",
                "slots": [
                    {
                        "key": key,
                        "value": value
                    } for key, value in tracker["entities"].items()
                ]
            },
            {
                "code": "bot_{}".format(str(i)),
                "nodeId": tracker["node_id"],
                "type": "2",  # 1、一问一答/2、多轮对话/3、闲聊
                "speaker": "2",  # 1 为用户，2为机器人
                "time": tracker["time_stamp"][1],
                "context": tracker["bot_response"],
                "understanding": "",
                "intent": "",
                "candidateIntent": "",
                "slots": []
            }
        ] for i, tracker in enumerate(self.get_logger_dict()["state_tracker"])]
        details = list(chain(*details))
        return {
            "id": self.user_id,
            "busiId": self.user_id,
            "robot": "社区矫正电话汇报机器人",
            "algorithmPlat": "小语智能问答平台",
            "source": "10",  # 对话来源（1手机、2固话、5互联网、10第三方业务系统）
            "souceMjobsark": "社区矫正汇报小程序",
            "startTime": self.startTime,
            "endTime": time.strftime('%Y-%m-%d %H:%M:%S'),
            "province": "",
            "city": "",
            "district": "",
            "status": StatusCode.get_xiaoyu_code(self.statues_code),
            "businessStatus": "",
            "dialog": {
                "globalSlots": globalSlots,
                "details": details,
            }
        }
