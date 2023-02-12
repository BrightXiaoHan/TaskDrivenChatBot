"""机器人资源、对话管理."""
import opencc

import xiaoyu.dialogue as dialogue
import xiaoyu.rpc.faq as faq
import xiaoyu.nlu as nlu
from xiaoyu.config import global_config
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
from xiaoyu.utils.funcs import async_get_rpc, async_post_rpc, get_time_stamp

DELAY_LODDING_ROBOT = global_config["_delay_loading_robot"]
MASTER_ADDR = global_config["master_addr"]
SENTIMENT_SERVER_URL = global_config.get("sentiment_server_url", "")

__all__ = [
    "session_reply",
    "delete",
    "push",
    "checkout",
    "graph_train",
    "nlu_train",
    "nlu_train_sync",
    "faq_train",
    "analyze",
    "cluster",
    "delete_graph",
    "sensitive_words",
    "sensitive_words_train",
    "dynamic_intent_train",
    "dynamic_intent_delete",
    "dynamic_qa_train",
    "dynamic_qa_delete",
]


OPENCC_CONVERTER = opencc.OpenCC("t2s.json")


async def _faq_session_reply(robot_code, session_id, user_says, faq_params={}):
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
    robot_code,
    session_id,
    user_says,
    user_code="",
    params={},
    faq_params={},
    traceback=False,
    flow_id=None,
):
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
    user_code
    if robot_code not in agents:
        # TODO 这里应当跟多轮对话的逻辑合并
        return_dict = await _faq_session_reply(robot_code, session_id, user_says, faq_params)
    else:
        agent = agents[robot_code]
        await agent.handle_message(user_says, sender_id=session_id, params=params, flow_id=flow_id)
        return_dict = agent.get_latest_xiaoyu_pack(session_id, traceback=traceback)

    return_dict["mood"] = await sentiment_analyze(user_says)
    return return_dict


async def sentiment_analyze(text):
    if SENTIMENT_SERVER_URL:
        url = "http://{}/xiaoyu/rpc/sentiment".format(SENTIMENT_SERVER_URL)
        sentiment = await async_get_rpc(url, {"text": text})
        return sentiment["score"]
    else:
        return -1


async def analyze(robot_code, text):
    """nlu分析接口.

    Args:
        robot_code (str): 机器人唯一标识
        text (str): 待分析的文本

    Returns:
        dict: 具体参见nlu.
    """
    # 由于analyze接口对应的机器人往往只有语义理解模型，新训练的机器人往往没有被加载
    # 这里加载一下，如果此次加载没有加载到，再抛出异常
    if robot_code not in robots_interpreters:
        try:
            version = nlu.get_using_model(robot_code)
            robots_interpreters[robot_code] = nlu.get_interpreter(robot_code, version)
        except Exception:
            raise NoAvaliableModelException(robot_code, "latest", MODEL_TYPE_NLU)
    interperter = robots_interpreters.get(robot_code)

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

    # 远程rpc情感分析, TODO 与nlu模块结合
    if SENTIMENT_SERVER_URL:
        url = "http://{}/xiaoyu/rpc/sentiment".format(SENTIMENT_SERVER_URL)
        sentiment = await async_get_rpc(url, {"text": text})
        result_dict["sentiment"] = sentiment["confidence"]

    return result_dict


def delete(robot_code):
    """删除整个机器人.

    Args:
        robot_code (str): 机器人唯一标识

    Returns:
        dict: {'status_code': 0}
    """
    # TODO 正式环境中如何进行同步
    # 停止已经加载的机器人
    agents.pop(robot_code, None)
    # 删除faq中的所有数据
    faq.faq_delete_all(robot_code)
    # 删除nlu相关模型
    nlu.delete_robot(robot_code, force=True)
    # 删除对话流程配置
    dialogue.delete_robot(robot_code)

    return {"status_code": 0}


def delete_graph(robot_code, graph_id):
    """删除某个机器人的某个对话流程配置.

    Args:
        robot_code (str): 机器人唯一标识
        graph_id (str): 流程唯一标识

    Returns:
        dict: {'status_code': 0}
    """
    # TODO 正式环境中如何进行同步
    # 删除对话流程配置
    dialogue.delete_graph(robot_code, graph_id)
    # 删除内存中的对话流程配置
    if robot_code in agents:
        agents[robot_code].delete_dialogue_graph(graph_id)
    return {"status_code": 0}


async def push(robot_code, version):
    """将某个版本的模型推送到正式环境.

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 对应模型或配置的版本
    """
    # 如果没有指定master_addr则什么都不做
    if not MASTER_ADDR:
        return {"status_code": 0}
    # 推送对话流程配置
    dialogue_graphs = dialogue.get_graph_data(robot_code, version)
    for graph_data in dialogue_graphs.values():
        data = {
            "robot_id": robot_code,
            "method": "train",
            "version": version,
            "data": graph_data,
        }
        await async_post_rpc("http://{}/xiaoyu/multi/graph".format(MASTER_ADDR), data)

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
        await async_post_rpc("http://{}/xiaoyu/multi/nlu".format(MASTER_ADDR), data)

    # 推送faq
    await faq.faq_push(robot_code)
    return {"status_code": 0}


def _load_latest(robot_code, graph_id=None):
    """加载最新的模型."""
    try:
        version = nlu.get_using_model(robot_code)
        interpreter = nlu.get_interpreter(robot_code, version)
        if not DELAY_LODDING_ROBOT:
            robots_interpreters[robot_code] = interpreter
    except (AssertionError, NoAvaliableModelException, FileNotFoundError):
        interpreter = nlu.get_empty_interpreter(robot_code)
    graphs = dialogue.get_graph_data(robot_code)
    if graph_id:
        # 如果指定了机器人id则只加载指定id的对话流程
        assert graph_id in graphs, "机器人{}中没有找到id为{}的对话流程配置".format(robot_code, graph_id)
        graphs = {graph_id: graphs[graph_id]}

    agents[robot_code] = dialogue.Agent(robot_code, interpreter, graphs)


def checkout(robot_code, model_type, version):
    """将模型或配置回退到某个版本.

    Args:
        robot_code (str): 机器人唯一标识
        model_type (str): 类型，参见utils.define.MODEL_TYPE_*
                          目前仅支持nlu模型，对话流程配置
        version (str): 对应模型或配置的版本
    """
    if robot_code not in agents:
        _load_latest(robot_code)
    if model_type == MODEL_TYPE_NLU:
        interpreter = nlu.get_interpreter(robot_code, version)
        agents[robot_code].update_interpreter(interpreter=interpreter)
    elif model_type == MODEL_TYPE_DIALOGUE:
        graph = dialogue.checkout(robot_code, version)
        for graph_data in graph.values():
            agents[robot_code].update_dialogue_graph(graph_data)
    else:
        raise ModelTypeException(model_type)
    return None


def nlu_train(robot_code, version, data, _convert=True):
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
    return {"status_code": 0}


def graph_train(robot_code, version, data):
    """更新对话流程配置。更新配置后直接生效.

    Args:
        robot_code (str): 机器人唯一标识
        version (str): nlu数据版本号
        data (dict): 前端配置生成的对话流程配置数据
    """
    # 更新数据
    dialogue.update_dialogue_graph(robot_code, version, data)

    # 更新机器人中的数据
    if robot_code in agents:
        agents[robot_code].update_dialogue_graph(data)
    else:
        assert "id" in data, "对话流程配置中应当包含id字段"
        _load_latest(robot_code, data["id"])
    return {"status_code": 0}


def cluster(robot_code):
    """未识别问题的归集与整理.

    Args:
        robot_code (str): 机器人唯一标识
    """
    nlu.run_cluster(robot_code)
    return {"status_code": 0}


def sensitive_words_train(robot_code, words, label):
    nlu.save_sensitive_words_to_file(robot_code, words, label)
    searcher = nlu.get_sensitive_words_searcher(robot_code, label)
    if robot_code not in sensitive_words_searchers:
        sensitive_words_searchers[robot_code] = {}
    sensitive_words_searchers[robot_code][label] = searcher
    return {"status_code": 0}


async def sensitive_words(robot_code, text, labels, strict=True):
    # TODO 检查 robot_code 是否存在
    text = OPENCC_CONVERTER.convert(text)
    searchers = sensitive_words_searchers[robot_code]

    sensitive_words = []
    masked_text = text
    for label in labels:
        if label not in searchers:
            raise RuntimeError("机器人{}中没有找到标签为{}的敏感词搜索器".format(robot_code, label))
        searcher = searchers[label]
        words, masked_text = searcher.FindAll(masked_text, strict=strict)
        sensitive_words.extend(words)

    sentiment = await sentiment_analyze(text)

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

if DELAY_LODDING_ROBOT:
    agents = {}
    sensitive_words_searchers = {}
else:
    sensitive_words_searchers = nlu.load_all_sensitive_words_searcher()
    # 启动程序时加载所有机器人到缓存中
    robot_codes = dialogue.get_all_robot_code()
    robots_interpreters = nlu.load_all_using_interpreters()

    robots_graph = {robot_code: dialogue.get_graph_data(robot_code) for robot_code in robot_codes}

    agents = {}
    for robot_code in robot_codes:
        if robot_code not in robots_interpreters:
            robots_interpreters[robot_code] = nlu.get_empty_interpreter(robot_code)
            print("机器人{}不存在nlu训练数据，加载空的解释器".format(robot_code))
        try:
            agents[robot_code] = dialogue.Agent(robot_code, robots_interpreters[robot_code], robots_graph[robot_code])
        except DialogueStaticCheckException:
            print("加载机器人{}失败，请检查对话流程的配置。".format(robot_code))

        print("加载机器人{}成功".format(robot_code))
