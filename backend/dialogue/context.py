import re
import time

from utils.funcs import get_time_stamp
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
            slot_name: "" for slot_name in self.agent.slots_abilities}
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
        self.transfer_manual = False
        self.current_graph_id = ""

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
        self.transfer_manual = False

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

        latest_node_data = self._latest_msg().get_latest_node_data()
        if latest_node_data:
            msg.add_traceback_data(latest_node_data)
        
        # 记录消息
        self.msg_recorder.append(msg)

        def run():
            if self.current_state is None:
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
                        self.reset_status()
                        break
            if self.current_state is None:
                response = msg.get_faq_answer()
                self.state_recorder.append("faq")
                # 记录机器人返回的话术
                self.response_recorder.append(FAQ_FLAG)
                self.add_traceback_data({
                    "type": "faq",
                    "hit": msg.faq_result["title"],
                    "category": msg.faq_result.get("catagory", ""),
                    "confidence": msg.faq_result["confidence"],
                    "recall": msg.faq_result.get('recommendQuestions', [])
                })
            else:
                while True:
                    response = next(self.current_state)

                    if isinstance(response, str):
                        # 这种情况下是节点内部回复用户话术
                        response = self.decode_ask_words(response)
                        self.response_recorder.append(response)
                        break
                    elif response is not None:
                        # 这种情况下是节点进行切换
                        self.state_recorder.append(response.config["node_id"])
                        self.current_state = response(self)
                    else:
                        self.current_state = None
                        return run()
            return response

        run()
        # 小语平台执行轮数加一
        self.turn_id += 1

        # 记录小语平台时间
        end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.time_stamp_turns.append((start_time, end_time))
        return self.response_recorder[-1]

    def _latest_msg(self):
        if len(self.msg_recorder) == 0:
            # 机器人说节点触发时往往没有msg，这里创建一条空消息
            msg = self.agent.interpreter.parse("这是一条空消息")
            self.msg_recorder.append(msg)
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

    def get_latest_xiaoyu_pack(self):
        """
        获取小语对话工厂最近一次的对话数据
        """
        msg = self._latest_msg()
        faq_answer_meta = msg.faq_result
        recommendQuestions = faq_answer_meta.get('recommendQuestions', []) if self.response_recorder[-1] == FAQ_FLAG else []
        relatedQuest = faq_answer_meta.get("related_quesions", []) if self.response_recorder[-1] == FAQ_FLAG else []
        hotQuestions =  faq_answer_meta.get("hotQuestions", []) if self.response_recorder[-1] == FAQ_FLAG else []
        faq_id = msg.get_faq_id() if self.response_recorder[-1] == FAQ_FLAG else ""
        reply_mode = faq_answer_meta.get("reply_mode", "1")
        faq_answer = faq_answer_meta.get("answer", "")

        dialog = {
            "code": self.current_graph_id,
            "nodeId": self.state_recorder[-1],
            "is_end": self.is_end
        }

        return_data = {
                "sessionId": self.user_id,
                "type": "2",
                # "user_says": msg.text,
                "says": faq_answer,
                "userSays": msg.text,
                "trafficManual": self.transfer_manual,
                "faq_id": faq_id,
                "responseTime": get_time_stamp(),
                "dialog": dialog,
                "recommendQuestions": recommendQuestions,
                "relatedQuest": relatedQuest,
                "hotQuestions": hotQuestions,
                "optional": msg.options,
                "hit": faq_answer_meta["title"],
                "confidence": faq_answer_meta["confidence"],
                "category": faq_answer_meta.get("catagory", ""),
                "traceback": msg.get_xiaoyu_format_traceback_data()
            }

        if self.response_recorder[-1] == FAQ_FLAG:
            return_data["reply_mode"] = reply_mode
            return_data["type"] = 1
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
            } for key, value in msg.get_abilities().items()]
            slots = entities
            
            return_data.update({
                # 第一个请求为建立连接的请求，这些字段都应为空·
                "intent": intent if len(self.msg_recorder) > 1 else "",
                "slots": slots if len(self.msg_recorder) > 1 else [],
                "entities": entities if len(self.msg_recorder) > 1 else [],
                "says": self.response_recorder[-1]
            })
        return return_data
