import re
import time
import inspect

from utils.funcs import get_time_stamp
from utils.exceptions import DialogueRuntimeException
from utils.define import UNK


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
        type_recorder (list): 记录经过每个节点的类型信息
        msg_recorder (list): 每个元素是一个backend.nlu.Message对象，记录每轮对话用户的回复，和nlu理解信息。
        response_recorder (list): 每个元素记录机器人每一轮对话的回复内容
        start_time (str): 对话开始时间，为float格式，直接由time.time()得到
        turn_id (int): 当前对话轮数记录
        slot_setting_turns (dict): 槽位填充对应的对话轮数，key为槽位名称，value为轮数
        time_stamp_turns (list): 记录每一轮对话的时间，每个元素的格式为(开始时间，结束时间)
                                格式与start_time字段相同，列表元素个数与总的对话轮数相同。
        is_end (bool): 记录对话是否结束，True为结束，False为未结束。
        dialog_status (str): # 对话状态码。“0”为正常对话流程，“10”为用户主动转人工，“11”为未识别转人工，“20”为机器人挂断
        current_graph_id (str): 记录当前的对话流程术语那个对话流程id

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
            slot_name: "" for slot_name in self.agent.slots_abilities}
        self.params = params
        self.user_id = user_id
        self.current_state = None
        self.state_recorder = list()
        self.type_recorder = list()
        self.msg_recorder = list()
        self.response_recorder = list()
        self.start_time = time.time()
        self.turn_id = 0
        self.entity_setting_turns = {}
        self.time_stamp_turns = []
        self.is_end = False
        self.dialog_status = "0"
        self.current_graph_id = ""

    def update_params(self, params):
        """
        对话过程中更新全局参数所用

        Args:
            name (dict): 待更新的全局参数
        """
        if isinstance(params, dict):
            self.params.update(params)

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


    def switch_graph(self, graph_id, node_name):
        graph = self.agent.graphs.get(graph_id, None)
        if not graph:
            raise DialogueRuntimeException("切换流程图失败",
                                           self.robot_code, node_name)
        return graph[0]

    def reset_status(self):
        """
        重置对话状态
        """
        self.is_end = False
        self.transfer_manual = "0"

    def trigger(self):
        """
        对话重新开始对每个开始节点进行触发，也可以复用在对话流程当中需要跳出的情况

        Returns: 
            bool: 是否触发成功，触发成功未True，触发失败为False
        """
        for graph_id, graph in self.agent.graphs.items():
            if len(graph) == 0:
                # 防止空流程
                continue
            node = graph[0]
            if node.trigger(self):
                # 注意这里一定要先设置当前id，开始节点的调试信息会用到
                self.current_graph_id = graph_id
                self.current_state = node(self)
                self.state_recorder.append(node.config["node_id"])
                self.type_recorder.append(node.NODE_NAME)
                self.reset_status()
                return True

        return False

    async def perform_faq(self):
        """
        对话流程中触发FAQ，做出响应的操作
        """
        msg = self._latest_msg()
        await msg.perform_faq()
        response = msg.get_faq_answer()
        self.state_recorder.append("faq")
        self.type_recorder.append("faq")
        # 记录机器人返回的话术
        self.response_recorder.append(FAQ_FLAG)
        self.add_traceback_data({
            "type": "faq",
            "hit": msg.faq_result["title"],
            "category": msg.faq_result.get("catagory", ""),
            "confidence": msg.faq_result["confidence"],
            "recall": msg.faq_result.get('recommendQuestions', [])
        })
        return response

    async def handle_message(self, msg):
        """
        给定nlu模型给出的语义理解消息，处理消息记录上下文，并返回回复用户的话术
        Args:
            msg (backend.nlu.Message): 消息对象

        Return:
            str: 回复用户的话术
        """
        # 小语平台执行轮数加一
        self.turn_id += 1
        # 小语平台：记录起始时间
        start_time = get_time_stamp()

        latest_node_data = self._latest_msg().get_latest_node_data()
        if latest_node_data:
            msg.add_traceback_data(latest_node_data)
        
        # 记录消息
        self.msg_recorder.append(msg)

        async def run():
            if self.current_state is None:
                self.trigger()
            
            if self.current_state is None:
                # 如果没有触发任何流程，且faq有答案，走FAQ
                response = await self.perform_faq()
            
            elif self.current_state is None:
                # 如果即没有触发任何流程，且faq没有答案，走闲聊
                response = self.perform_chitchat()

            else:
                while True:
                    response = await self.current_state.__anext__()
                    if response == FAQ_FLAG:
                        # 对话流程内部触发FAQ
                        response = await self.perform_faq()
                        break
                    elif isinstance(response, str):
                        # 这种情况下是节点内部回复用户话术
                        response = self.decode_ask_words(response)
                        self.response_recorder.append(response)
                        break
                    elif response is not None:
                        # 这种情况下是节点进行切换
                        self.state_recorder.append(response.config["node_id"])
                        self.type_recorder.append(response.NODE_NAME)
                        self.current_state = response(self)
                    else:
                        self.current_state = None
                        return await run()
            return response

        await run()

        # 记录小语平台时间
        end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.time_stamp_turns.append((start_time, end_time))
        return self.response_recorder[-1]

    def _latest_msg(self):
        if len(self.msg_recorder) == 0:
            return self.agent.interpreter.get_empty_msg()
        return self.msg_recorder[-1]

    def add_traceback_data(self, data):
        """
        向调试信息数据添加一个记录节点，并记录到最近一个msg对象中
        """
        msg = self._latest_msg()
        msg.add_traceback_data(data)

    def update_traceback_datas(self, data):
        for key, value in data.items():
            self.update_traceback_data(key, value)

    def update_traceback_data(self, key, value):
        """
        记录节点运行过程中的追踪信息，并记录到最近的一个msg对象中
        """
        msg = self._latest_msg()

        # 当msg对象的调试数据为空时向其加载数据，将上一个数据的对象导入
        if msg.is_traceback_empty:
            raise DialogueRuntimeException(
                "禁止向空消息添加调试数据", self.robot_code, "unkown")

        msg.update_traceback_data(key, value)

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
                         params_replace_function, content)
        content = re.sub(r"\$\{_user_says}", self._latest_msg().text, content)
        content = re.sub(r"\$\{_robot_code}", self.robot_code, content)
        return content

    def get_latest_xiaoyu_pack(self, traceback=False):
        """
        获取小语对话工厂最近一次的对话数据
        """
        msg = self._latest_msg()

        dialog = {
            "code": self.current_graph_id,
            "nodeId": self.state_recorder[-1],
            "is_end": self.is_end,
            "nodeType": self.type_recorder[-1]
        }
        return_data = {
            "sessionId": self.user_id,
            "type": "2",
            "says": "",
            "userSays": msg.text,
            "dialog_status": self.dialog_status,
            "faq_id": UNK,
            "responseTime": get_time_stamp(),
            "dialog": dialog,
            "recommendQuestions": [],
            "relatedQuest": [],
            "hotQuestions": [],
            "optional": msg.options,
            "hit": "",
            "confidence": 0,
            "category": "",
            "understanding": msg.understanding
        }

        if traceback:
           return_data["traceback"] = msg.get_xiaoyu_format_traceback_data()

        if self.response_recorder[-1] == FAQ_FLAG:
            faq_answer_meta = msg.faq_result
            if faq_answer_meta["faq_id"] == UNK:
                msg.understanding = "3"
            
            return_data["recommendQuestions"] = faq_answer_meta.get('recommendQuestions', [])
            return_data["relatedQuest"] = faq_answer_meta.get("related_quesions", [])
            return_data["hotQuestions"] =  faq_answer_meta.get("hotQuestions", [])
            return_data["faq_id"] = msg.get_faq_id()

            return_data["says"] = msg.get_faq_answer()
            return_data["type"] = "1"
            
            reply_mode = faq_answer_meta.get("reply_mode", "1")
            if reply_mode != "1":
                return_data["sms_content"] = faq_answer_meta.get("sms_content", "")

        elif self.response_recorder[-1] != FAQ_FLAG:
            intent = {
                "understanding": msg.understanding,  # 1是已经理解，2是未理解
                "intent": msg.intent,
                "candidateIntent": []
            }
            entities = [{
                "key": key,
                "name": key,
                "value": value
            } for key, value in self.slots.items() if value and self.entity_setting_turns[key] == self.turn_id]
            slots = entities
            
            return_data.update({
                # 第一个请求为建立连接的请求，这些字段都应为空·
                "intent": intent if len(self.msg_recorder) > 1 else "",
                "slots": slots if len(self.msg_recorder) > 1 else [],
                "entities": entities if len(self.msg_recorder) > 1 else [],
                "says": self.response_recorder[-1]
            })
        return return_data
