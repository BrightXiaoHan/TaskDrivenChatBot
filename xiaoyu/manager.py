"""机器人资源、对话管理."""
from typing import Any, Dict, List, Optional

import opencc

import xiaoyu.dialogue as dialogue
import xiaoyu.nlu as nlu
import xiaoyu.rpc.faq as faq
import xiaoyu_interface.call as call
import xiaoyu_interface.paddlenlp as paddlenlp
from xiaoyu.config import XiaoyuConfig
from xiaoyu.utils.define import (
    MODEL_TYPE_DIALOGUE,
    MODEL_TYPE_NLU,
    UNK,
    get_chitchat_faq_id,
)
from xiaoyu.utils.exceptions import (
    DialogueStaticCheckException,
    ModelTypeException,
    NoAvaliableModelException,
)
from xiaoyu.utils.funcs import async_post_rpc, get_time_stamp

OPENCC_CONVERTER = opencc.OpenCC("t2s.json")


class RobotManager(object):
    def __init__(self, config: XiaoyuConfig) -> None:
        self.master_addr = config.master_addr
        self.delay_loading_robot = config.delay_loading_robot
        self.config = config

        self.sensitive_words_searchers = nlu.load_all_sensitive_words_searcher(config.model_storage_folder)
        # 启动程序时加载所有机器人到缓存中
        self.robot_codes = dialogue.get_all_robot_code(config.model_storage_folder)
        self.robots_interpreters = nlu.load_all_using_interpreters(config.model_storage_folder)

        self.robots_graph: Dict[str, Dict[str, Dict]] = {
            robot_code: dialogue.get_graph_data(robot_code) for robot_code in self.robot_codes
        }

        self.agents: Dict[str, dialogue.Agent] = {}
        for robot_code in self.robot_codes:
            if robot_code not in self.robots_interpreters:
                self.robots_interpreters[robot_code] = nlu.get_empty_interpreter(robot_code)
                print("机器人{}不存在nlu训练数据，加载空的解释器".format(robot_code))
            try:
                self.agents[robot_code] = dialogue.Agent(
                    robot_code, self.robots_interpreters[robot_code], self.robots_graph[robot_code]
                )
            except DialogueStaticCheckException:
                print("加载机器人{}失败，请检查对话流程的配置。".format(robot_code))
            print("加载机器人{}成功".format(robot_code))

    @property
    def is_master(self) -> bool:
        return self.master_addr is not None

    async def _faq_session_reply(
        self, robot_code: str, session_id: str, user_says: str, faq_params: Dict[str, str] = {}
    ) -> Dict[str, Any]:
        """当不存在多轮对话配置时，直接调用faq的api."""
        faq_answer_meta = await faq.faq_ask(robot_code, user_says, faq_params)

        if faq_answer_meta["faq_id"] == UNK:
            says = await faq.faq_chitchat_ask(get_chitchat_faq_id(robot_code), user_says)
        else:
            says = faq_answer_meta["answer"]

        return {
            "sessionId": session_id,
            "type": "1",
            # "user_says": self.latest_msg().text,
            "says": says,
            "userSays": user_says,
            "faq_id": faq_answer_meta["faq_id"],
            "responseTime": get_time_stamp(),
            "recommendQuestions": faq_answer_meta["recommendQuestions"],
            "recommendScores": faq_answer_meta["recommendScores"],
            "relatedQuest": faq_answer_meta.get("related_quesions", []),
            "hotQuestions": faq_answer_meta["hotQuestions"],
            "hit": faq_answer_meta["title"],
            "confidence": faq_answer_meta["confidence"],
            "category": faq_answer_meta.get("catagory", ""),
            "reply_mode": faq_answer_meta.get("reply_mode", "1"),
            "sms_content": faq_answer_meta.get("sms_content", ""),
            "understanding": faq_answer_meta.get("understanding", "3"),  # 0为已经理解，3为未理解faq
            "dialog_status": "0",  # 对话状态码。“0”为正常对话流程，“10”为用户主动转人工，“11”为未识别转人工，“20”为机器人挂断
        }

    async def session_reply(
        self,
        robot_code: str,
        session_id: str,
        user_says: str,
        user_code: str = "",
        params: Dict[str, Any] = {},
        faq_params: Dict[str, str] = {},
        traceback: bool = False,
        flow_id: str = None,
    ) -> Dict[str, Any]:
        """与用户进行对话接口.

        Args:
            robot_code (str): 机器人唯一标识
            session_id (str): 会话唯一标识
            user_says (str): 用户对机器人说的内容
            user_code (str): 用户id，现在session_reply接口可以和session_create接口合并，当时新建立的会话时，需要传递此参数
            params (dict): 全局参数，现在session_reply接口可以和session_create接口合并，当时新建立的会话时，需要传递此参数
            faq_params (int): faq 相关参数
            traceback (bool): 是否返回调试信息
            flow_id (str): 如果指定改参数，可以强制启动某个流程

        Returns:
            dict: 具体参见context.StateTracker.get_latest_xiaoyu_pack
        """
        if robot_code not in self.agents:
            # TODO 这里应当跟多轮对话的逻辑合并
            return_dict = await self._faq_session_reply(robot_code, session_id, user_says, faq_params)
        else:
            agent = self.agents[robot_code]
            await agent.handle_message(user_says, sender_id=session_id, params=params, flow_id=flow_id)
            return_dict = agent.get_latest_xiaoyu_pack(session_id, traceback=traceback)

        return_dict["mood"] = await self.sentiment_analyze(user_says)
        return return_dict

    async def sentiment_analyze(self, text: str) -> float:
        input = paddlenlp.SentimentAnalysisInputExample(text=text)
        output: paddlenlp.SentimentAnalysisOutputExmaple = await call.sentiment_analysis(input)
        return output.score

    async def analyze(self, robot_code: str, text: str) -> Dict[str, Any]:
        """nlu分析接口.

        Args:
            robot_code (str): 机器人唯一标识
            text (str): 待分析的文本

        Returns:
            dict: 具体参见nlu.
        """
        # 由于analyze接口对应的机器人往往只有语义理解模型，新训练的机器人往往没有被加载
        # 这里加载一下，如果此次加载没有加载到，再抛出异常
        if robot_code not in self.robots_interpreters:
            try:
                version = nlu.get_using_model(robot_code)
                self.robots_interpreters[robot_code] = nlu.get_interpreter(robot_code, version)
            except Exception:
                raise NoAvaliableModelException(robot_code, "latest", MODEL_TYPE_NLU)
        interperter = self.robots_interpreters.get(robot_code)

        # TODO 分析接口目前走的是ngram匹配，这里后续需要改成语义向量分析
        msg = await interperter.parse(text, use_model=False, parse_internal_ner=True)
        result_dict = msg.to_dict()

        # 按照欧的要求，将命名实体的返回格式做修正
        if "entities" in result_dict:
            result_dict["entities"] = [
                {
                    "type": key,
                    "value": value,
                }
                for key, values in result_dict["entities"].items()
                for value in values
            ]

        result_dict["sentiment"] = await self.sentiment_analyze(text)
        return result_dict

    def delete(self, robot_code: str) -> None:
        """删除整个机器人.

        Args:
            robot_code (str): 机器人唯一标识

        Returns:
            dict: {'status_code': 0}
        """
        # TODO 正式环境中如何进行同步
        # 停止已经加载的机器人
        self.agents.pop(robot_code, None)
        # 删除faq中的所有数据
        faq.faq_delete_all(robot_code, is_master=self.is_master)
        # 删除nlu相关模型
        nlu.delete_robot(self.config.model_storage_folder, robot_code, force=True)
        # 删除对话流程配置
        dialogue.delete_robot(self.config.graph_storage_folder, robot_code)

    def delete_graph(self, robot_code: str, graph_id: str) -> None:
        """删除某个机器人的某个对话流程配置.

        Args:
            robot_code (str): 机器人唯一标识
            graph_id (str): 流程唯一标识

        Returns:
            dict: {'status_code': 0}
        """
        # TODO 正式环境中如何进行同步
        # 删除对话流程配置
        dialogue.delete_graph(self.config.graph_storage_folder, robot_code, graph_id)
        # 删除内存中的对话流程配置
        if robot_code in self.agents:
            self.agents[robot_code].delete_dialogue_graph(graph_id)
        return {"status_code": 0}

    async def push(self, robot_code: str, version: str):
        """将某个版本的模型推送到正式环境.

        Args:
            robot_code (str): 机器人唯一标识
            version (str): 对应模型或配置的版本
        """
        # 如果没有指定master_addr则什么都不做
        if self.is_master:
            return
        # 推送对话流程配置
        dialogue_graphs = dialogue.get_graph_data(self.config.graph_storage_folder, robot_code, version)
        for graph_data in dialogue_graphs.values():
            data = {
                "robot_id": robot_code,
                "method": "train",
                "version": version,
                "data": graph_data,
            }
            await async_post_rpc("http://{}/xiaoyu/multi/graph".format(self.master_addr), data)

        # 推送nlu模型
        nlu_data = nlu.get_nlu_raw_data(robot_code, version)
        if nlu_data:
            data = {
                "robot_id": robot_code,
                "method": "train",
                "version": version,
                "data": nlu_data,
                "_convert": False,
            }
            await async_post_rpc("http://{}/xiaoyu/multi/nlu".format(self.master_addr), data)

        # 推送faq
        await faq.faq_push(robot_code, self.is_master)
        return {"status_code": 0}

    def _load_latest(self, robot_code: str, graph_id: Optional[str] = None):
        """加载最新的模型."""
        try:
            version = nlu.get_using_model(robot_code)
            interpreter = nlu.get_interpreter(robot_code, version)
            if not self.config.delay_loading_robot:
                self.robots_interpreters[robot_code] = interpreter
        except (AssertionError, NoAvaliableModelException, FileNotFoundError):
            interpreter = nlu.get_empty_interpreter(robot_code)
        graphs = dialogue.get_graph_data(self.config.graph_storage_folder, robot_code)
        if graph_id:
            # 如果指定了机器人id则只加载指定id的对话流程
            assert graph_id in graphs, "机器人{}中没有找到id为{}的对话流程配置".format(robot_code, graph_id)
            graphs = {graph_id: graphs[graph_id]}

        self.agents[robot_code] = dialogue.Agent(robot_code, interpreter, graphs)

    def checkout(self, robot_code: str, model_type: str, version: str) -> None:
        """将模型或配置回退到某个版本.

        Args:
            robot_code (str): 机器人唯一标识
            model_type (str): 类型，参见utils.define.MODEL_TYPE_*
                              目前仅支持nlu模型，对话流程配置
            version (str): 对应模型或配置的版本
        """
        if robot_code not in self.agents:
            self._load_latest(robot_code)
        if model_type == MODEL_TYPE_NLU:
            interpreter = nlu.get_interpreter(robot_code, version)
            self.agents[robot_code].update_interpreter(interpreter=interpreter)
        elif model_type == MODEL_TYPE_DIALOGUE:
            graph = dialogue.checkout(robot_code, version)
            for graph_data in graph.values():
                self.agents[robot_code].update_dialogue_graph(graph_data)
        else:
            raise ModelTypeException(model_type)

    def nlu_train(self, robot_code: str, version: str, data: Dict, _convert: bool = True) -> None:
        """更新nlu训练数据，这里只更新配置，不进行训练。训练操作会发送到训练进程异步进行.

        Args:
            robot_code (str): 机器人唯一标识
            version (str): nlu数据版本号
            data (dict): 前端配置生成的nlu模型训练数据
            _convert (bool): 是否对传来的数据进行转换。
                    (从前端直接传来的数据需要转换，push过来的数据不需要转换)
                    default is False
        """
        nlu.update_training_data(robot_code, version, data, _convert)

    def graph_train(self, robot_code, version, data):
        """更新对话流程配置。更新配置后直接生效.

        Args:
            robot_code (str): 机器人唯一标识
            version (str): nlu数据版本号
            data (dict): 前端配置生成的对话流程配置数据
        """
        # 更新数据
        dialogue.update_dialogue_graph(robot_code, version, data)

        # 更新机器人中的数据
        if robot_code in self.agents:
            self.agents[robot_code].update_dialogue_graph(data)
        else:
            assert "id" in data, "对话流程配置中应当包含id字段"
            self._load_latest(robot_code, data["id"])

    def cluster(robot_code: str) -> None:
        """未识别问题的归集与整理.

        Args:
            robot_code (str): 机器人唯一标识
        """
        nlu.run_cluster(robot_code)

    def sensitive_words_train(self, robot_code: str, words: List[str], label: str):
        nlu.save_sensitive_words_to_file(robot_code, words, label)
        searcher = nlu.get_sensitive_words_searcher(robot_code, label)
        if robot_code not in self.sensitive_words_searchers:
            self.sensitive_words_searchers[robot_code] = {}
        self.sensitive_words_searchers[robot_code][label] = searcher

    async def sensitive_words(self, robot_code: str, text: str, labels: List[str], strict: bool = True):
        # TODO 检查 robot_code 是否存在
        text = OPENCC_CONVERTER.convert(text)
        searchers = self.sensitive_words_searchers[robot_code]

        sensitive_words = []
        masked_text = text
        for label in labels:
            if label not in searchers:
                raise RuntimeError("机器人{}中没有找到标签为{}的敏感词搜索器".format(robot_code, label))
            searcher = searchers[label]
            words, masked_text = searcher.FindAll(masked_text, strict=strict)
            sensitive_words.extend(words)
        sentiment = await self.sentiment_analyze(text)
        return {
            "text": text,
            "masked_text": masked_text,
            "sensitive_words": sensitive_words,
            "sentiment": sentiment,
        }

    # 引入其他模块的方法
    faq_train = faq.faq_update
    nlu_train_sync = nlu.train_robot
    dynamic_intent_train = dialogue.dynamic_intent_train
    dynamic_qa_train = dialogue.dynamic_qa_train
    dynamic_qa_delete = dialogue.dynamic_qa_delete
    dynamic_intent_delete = dialogue.dynamic_intent_delete
