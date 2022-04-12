"""
机器人资源、对话管理
"""
import backend.nlu as nlu
import backend.dialogue as dialogue
import backend.faq as faq

from utils.exceptions import DialogueStaticCheckException, ModelTypeException, NoAvaliableModelException
from utils.funcs import get_time_stamp, async_post_rpc, async_get_rpc
from utils.define import MODEL_TYPE_DIALOGUE, MODEL_TYPE_NLU

from config import global_config

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
    "analyze"
]


async def _faq_session_reply(robot_code, session_id, user_says, faq_params={}):
    """
    当不存在多轮对话配置时，直接调用faq的api
    """
    faq_answer_meta = await faq.faq_ask(robot_code, user_says, faq_params)
    return {
        "sessionId": session_id,
        "type": "1",
        # "user_says": self._latest_msg().text,
        "says": faq_answer_meta["answer"],
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
        "understanding": faq_answer_meta.get("understanding", "3")  # 0为已经理解，3为未理解faq
    }


async def session_reply(robot_code,
                  session_id,
                  user_says,
                  user_code="",
                  params={},
                  faq_params={},
                  traceback=False):
    """与用户进行对话接口

    Args:
        robot_code (str): 机器人唯一标识
        session_id (str): 会话唯一标识
        user_says (str): 用户对机器人说的内容
        user_code (str): 用户id，现在session_reply接口可以和session_create接口合并，当时新建立的会话时，需要传递此参数
        params (dict): 全局参数，现在session_reply接口可以和session_create接口合并，当时新建立的会话时，需要传递此参数
        faq_params (int): faq 相关参数
        traceback (bool): 是否返回调试信息

    Returns:
        dict: 具体参见context.StateTracker.get_latest_xiaoyu_pack
    """
    if robot_code not in agents:
        return_dict = await _faq_session_reply(robot_code, session_id, user_says,
                                  faq_params)
    else:
        agent = agents[robot_code]
        await agent.handle_message(user_says, session_id, params)
        return_dict = agent.get_latest_xiaoyu_pack(session_id, traceback=traceback)
    
    # 远程rpc情感分析, TODO 与nlu模块结合
    if SENTIMENT_SERVER_URL:
        url = "http://{}/xiaoyu/rpc/sentiment".format(SENTIMENT_SERVER_URL)
        sentiment = await async_get_rpc(url, {"text": user_says})
        return_dict["mood"] = sentiment["score"]
    return return_dict


async def analyze(robot_code, text):
    """nlu分析接口

    Args:
        robot_code (str): 机器人唯一标识
        text (str): 待分析的文本

    Returns:
        dict: 具体参见nlu.
    """
    interperter = robots_interpreters.get(robot_code, None)

    if not interperter:
        raise NoAvaliableModelException(robot_code, "latest", MODEL_TYPE_NLU)

    # TODO 分析接口目前走的是ngram匹配，这里后续需要改成语义向量分析
    msg = await interperter.parse(text)
    result_dict = msg.to_dict()

    # 远程rpc情感分析, TODO 与nlu模块结合
    if SENTIMENT_SERVER_URL:
        url = "http://{}/xiaoyu/rpc/sentiment".format(SENTIMENT_SERVER_URL)
        sentiment = await async_get_rpc(url, {"text": text})
        result_dict["sentiment"] = sentiment["confidence"]

    return result_dict


def delete(robot_code):
    """删除整个机器人

    Args:
        robot_code (str): 机器人唯一标识

    Returns:
        dict: {'status_code': 0}
    """
    # 停止已经加载的机器人
    agents.pop(robot_code, None)
    # 删除faq中的所有数据
    faq.faq_delete_all(robot_code)
    # 删除nlu相关模型
    nlu.delete_robot(robot_code, force=True)
    # 删除对话流程配置
    dialogue.delete_robot(robot_code)

    return {'status_code': 0}


async def push(robot_code, version):
    """将某个版本的模型推送到正式环境

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 对应模型或配置的版本
    """
    # 如果没有指定master_addr则什么都不做
    if not MASTER_ADDR:
        return {'status_code': 0}
    # 推送对话流程配置
    dialogue_graphs = dialogue.get_graph_data(robot_code, version)
    for graph_data in dialogue_graphs.values():
        data = {
            "robot_id": robot_code,
            "method": "train",
            "version": version,
            "data": graph_data
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
            "_convert": False
        }
        await async_post_rpc("http://{}/xiaoyu/multi/nlu".format(MASTER_ADDR), data)

    # 推送faq
    await faq.faq_push(robot_code)
    return {'status_code': 0}


def _load_latest(robot_code, graph_id=None):
    """加载最新的模型
    """
    try:
        version = nlu.get_using_model(robot_code)
        interpreter = nlu.get_interpreter(robot_code, version)
    except (AssertionError, NoAvaliableModelException, FileNotFoundError):
        interpreter = nlu.get_empty_interpreter(robot_code)
    graphs = dialogue.get_graph_data(robot_code)
    if graph_id:
        # 如果指定了机器人id则只加载指定id的对话流程
        assert graph_id in graphs, "机器人{}中没有找到id为{}的对话流程配置".format(robot_code, graph_id)
        graphs = {graph_id: graphs[graph_id]}

    agents[robot_code] = dialogue.Agent(robot_code, interpreter, graphs)


def checkout(robot_code, model_type, version):
    """将模型或配置回退到某个版本

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
    """更新nlu训练数据，这里只更新配置，不进行训练。
       训练操作会发送到训练进程异步进行

    Args:
        robot_code (str): 机器人唯一标识
        version (str): nlu数据版本号
        data (dict): 前端配置生成的nlu模型训练数据
        _convert (bool): 是否对传来的数据进行转换。
                (从前端直接传来的数据需要转换，push过来的数据不需要转换)
                default is False
    """
    nlu.update_training_data(robot_code, version, data, _convert)
    return {'status_code': 0}


def graph_train(robot_code, version, data):
    """更新对话流程配置。更新配置后直接生效

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
    return {'status_code': 0}


# 引入其他模块的方法
faq_train = faq.faq_update
nlu_train_sync = nlu.train_robot

if DELAY_LODDING_ROBOT:
    agents = {}
else:
    # 启动程序时加载所有机器人到缓存中
    robot_codes = dialogue.get_all_robot_code()
    robots_interpreters = nlu.load_all_using_interpreters()
    robots_graph = {
        robot_code: dialogue.get_graph_data(robot_code)
        for robot_code in robot_codes
    }

    agents = {}
    for robot_code in robot_codes:
        if robot_code not in robots_interpreters:
            robots_interpreters[robot_code] = nlu.get_empty_interpreter(robot_code)
            print("机器人{}不存在nlu训练数据，加载空的解释器".format(robot_code))
        try:
            agents[robot_code] = dialogue.Agent(
                    robot_code, robots_interpreters[robot_code],
                    robots_graph[robot_code])
        except DialogueStaticCheckException:
            print("加载机器人{}失败，请检查对话流程的配置。".format(robot_code))
            
        print("加载机器人{}成功".format(robot_code))

