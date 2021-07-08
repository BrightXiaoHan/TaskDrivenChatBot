"""
机器人资源、对话管理
"""
import backend.nlu as nlu
import backend.dialogue as dialogue
import backend.faq as faq

from utils.exceptions import DialogueStaticCheckException, ModelTypeException
from utils.funcs import get_time_stamp, generate_uuid, post_rpc
from utils.define import MODEL_TYPE_DIALOGUE, MODEL_TYPE_NLU

from config import global_config

DELAY_LODDING_ROBOT = global_config["_delay_loading_robot"]
MASTER_ADDR = global_config["master_addr"]

__all__ = [
    "session_create", "session_reply", "delete", "push", "checkout",
    "graph_train", "nlu_train", "nlu_train_sync", "faq_train"
]


def session_create(robot_code, user_code, params):
    """建立会话连接

    Args:
        robot_code (str): 机器人唯一标识
        user_code (str): 用户id
        params (dict): 全局参数

    Returns:
        dict: 回复用户内容以及其他meta类型信息
              sessionId: 由AI后台创建的会话唯一id
              type: 问答类型："1"、一问一答 "2"、多轮对话 "3"、闲聊
              responseTime: 机器人回复的时间戳
              says: 机器人回复用户的内容
    """
    conversation_id = generate_uuid()
    if robot_code in agents:
        agent = agents[robot_code]
        response = agent.establish_connection(conversation_id, params)
    else:
        # 当没有找到相应机器人id的agent时，退化为faq机器人
        response = ""
    return {
        "sessionId": conversation_id,
        "type": "2",
        "responseTime": get_time_stamp(),
        "says": response
    }


def _faq_session_reply(robot_code, session_id, user_says, faq_params={}):
    """
    当不存在多轮对话配置时，直接调用faq的api
    """
    faq_answer_meta = faq.faq_ask(robot_code, user_says, faq_params)
    recommendQuestions = faq_answer_meta.get('recommendQuestions', [])
    relatedQuest = faq_answer_meta.get("similar_questions", [])
    hotQuestions = faq_answer_meta.get("hotQuestions", [])
    faq_answer = faq_answer_meta["answer"]
    faq_id = faq_answer_meta["faq_id"]
    return {
        "sessionId": session_id,
        # "user_says": self._latest_msg().text,
        "says": faq_answer,
        "userSays": user_says,
        "faq_id": faq_id,
        "responseTime": get_time_stamp(),
        "recommendQuestions": recommendQuestions,
        "relatedQuest": relatedQuest,
        "hotQuestions": hotQuestions
    }


def session_reply(robot_code, session_id, user_says, user_code="", params={}, faq_params={}):
    """与用户进行对话接口

    Args:
        robot_code (str): 机器人唯一标识
        session_id (str): 会话唯一标识
        user_says (str): 用户对机器人说的内容
        user_code (str): 用户id，现在session_reply接口可以和session_create接口合并，当时新建立的会话时，需要传递此参数
        params (dict): 全局参数，现在session_reply接口可以和session_create接口合并，当时新建立的会话时，需要传递此参数
        faq_params (int): faq 相关参数

    Returns:
        dict: 具体参见context.StateTracker.get_latest_xiaoyu_pack
    """
    if robot_code not in agents:
        return _faq_session_reply(robot_code, session_id, user_says, faq_params)

    agent = agents[robot_code]
    # 如果会话不存在，则根据传过来的session_id创建对话
    if not agent.session_exists(session_id):
        agent.establish_connection(session_id, params)
    agent.handle_message(user_says, session_id)
    return agent.get_latest_xiaoyu_pack(session_id)


def delete(robot_code):
    """删除整个机器人

    Args:
        robot_code (str): 机器人唯一标识

    Returns:
        dict: {'status_code': 0}
    """
    # 删除faq中的所有数据
    faq.faq_delete_all(robot_code)
    # 删除nlu相关模型
    nlu.delete_robot(robot_code, force=True)
    # 删除对话流程配置
    dialogue.delete_robot(robot_code)

    return {'status_code': 0}


def push(robot_code, version):
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
    for graph_data in dialogue_graphs:
        data = {
            "robot_id": robot_code,
            "method": "train",
            "version": version,
            "data": graph_data
        }
        post_rpc(
            "http://{}/xiaoyu/multi/graph".format(MASTER_ADDR), data)

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
        post_rpc("http://{}/xiaoyu/multi/nlu".format(MASTER_ADDR), data)

    # 推送faq
    faq.faq_push(robot_code)
    return {'status_code': 0}


def _load_latest(robot_code):
    """加载最新的模型
    """
    version = nlu.get_using_model(robot_code)
    interpreter = nlu.get_interpreter(robot_code, version)
    graphs = dialogue.get_graph_data(robot_code)

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
        _load_latest(robot_code)

    return {'status_code': 0}


# 引入其他模块的方法
faq_train = faq.faq_update
nlu_train_sync = nlu.train_robot

if DELAY_LODDING_ROBOT:
    agents = {}
else:
    # 启动程序时加载所有机器人到缓存中
    robots_interpreters = nlu.load_all_using_interpreters()
    robots_graph = {
        robot_code: dialogue.get_graph_data(robot_code)
        for robot_code in robots_interpreters
    }

    # 获取所有可用的robot_code
    robot_codes = [
        robot_code for robot_code, graph in robots_graph.items() if graph
    ]

    agents = {}
    for robot_code in robot_codes:
        try:
            agents[robot_code] = dialogue.Agent(robot_code, robots_interpreters[robot_code],
                                                robots_graph[robot_code])
        except DialogueStaticCheckException:
            continue
