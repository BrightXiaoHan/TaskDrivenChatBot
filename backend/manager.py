"""
机器人资源、对话管理
"""
import backend.nlu as nlu
import backend.dialogue as dialogue
import backend.faq as faq

from utils.exceptions import RobotNotFoundException, ModelTypeException
from utils.funcs import get_time_stamp, generate_uuid
from utils.define import MODEL_TYPE_DIALOGUE, MODEL_TYPE_NLU

__all__ = ["session_create",
           "session_reply",
           "delete",
           "push",
           "checkout",
           "graph_train",
           "nlu_train"]

robots_interpreters = nlu.load_all_using_interpreters()
robots_graph = {robot_code: dialogue.get_graph_data(robot_code)
                for robot_code in robots_interpreters}

# 获取所有可用的robot_code
robot_codes = [robot_code for robot_code,
               graph in robots_graph.items() if graph]

agents = {robot_code: dialogue.Agent(
    robot_code, robots_interpreters[robot_code], robots_graph[robot_codes])
    for robot_code in robot_codes}


def session_create(robot_code, user_code):
    """建立会话连接

    Args:
        robot_code (str): 机器人唯一标识
        user_code (str): 用户id

    Returns:
        dict: 回复用户内容以及其他meta类型信息
              sessionId: 由AI后台创建的会话唯一id
              type: 问答类型："1"、一问一答 "2"、多轮对话 "3"、闲聊
              responseTime: 机器人回复的时间戳
              says: 机器人回复用户的内容
    """
    if robot_code not in agents:
        raise RobotNotFoundException(robot_code)

    agent = agents[robot_code]
    response = agent.handle_message("建立连接")
    return {
        "sessionId": generate_uuid(),
        "type": "2",
        "responseTime": get_time_stamp(),
        "says": response
    }


def session_reply(robot_code, session_id, user_says):
    """与用户进行对话接口

    Args:
        robot_code (str): 机器人唯一标识
        session_id (str): 会话唯一标识
        user_says (str): 用户对机器人说的内容

    Returns:
        dict: 具体参见context.StateTracker.get_latest_xiaoyu_pack
    """
    if robot_code not in agents:
        raise RobotNotFoundException(robot_code)
    agent = agents[robot_code]
    agent.handle_message(user_says, session_id)
    return agent.get_latest_xiaoyu_pack()


def delete(robot_code):
    """删除整个机器人

    Args:
        robot_code (str): 机器人唯一标识

    Returns:
        dict: {'status_code': 0}
    """
    # 停用机器人
    agents.pop(robot_code, None)
    # 删除faq中的所有数据
    faq.faq_delete_all(robot_code)
    # 删除nlu相关模型
    nlu.delete_robot(robot_code, force=True)
    # 删除对话流程配置
    dialogue.delete_robot(robot_code)

    return {'status_code': 0}


def push(robot_code, model_type, version):
    """将某个版本的模型推送到正式环境

    Args:
        robot_code (str): 机器人唯一标识
        model_type (str): 类型，参见utils.define.MODEL_TYPE_*
        version (str): 对应模型或配置的版本
    """
    # TODO
    return None


def _load_latest(robot_code):
    """加载最新的模型
    """
    try:
        version = nlu.get_using_model(robot_code)
        interpreter = nlu.get_interpreter(robot_code, version)
        graph = dialogue.get_graph_data(robot_code)
    except Exception:
        return
    agents[robot_code] = dialogue.Agent(robot_code, interpreter, graph)


def checkout(robot_code, model_type, version):
    """将模型或配置回退到某个版本

    Args:
        robot_code (str): 机器人唯一标识
        model_type (str): 类型，参见utils.define.MODEL_TYPE_*
                          目前仅支持nlu模型，对话流程配置
        version (str): 对应模型或配置的版本
    """

    if model_type == MODEL_TYPE_NLU:
        interpreter = nlu.get_interpreter(robot_code, version)
        if robot_code in agents:
            agents[robot_code].update(interpreter=interpreter)
        else:
            _load_latest(robot_code)
    elif model_type == MODEL_TYPE_DIALOGUE:
        graph = dialogue.checkout(robot_code, version)
        if robot_code in agents:
            agents[robot_code].update(dialogue_graph=graph)
        else:
            _load_latest(robot_code)
    else:
        raise ModelTypeException(model_type)
    return None


def nlu_train(robot_code, version, data):
    """更新nlu训练数据，这里只更新配置，不进行训练。
       训练操作会发送到训练进程异步进行

    Args:
        robot_code (str): 机器人唯一标识
        version (str): nlu数据版本号
        data (dict): 前端配置生成的nlu模型训练数据
    """
    nlu.update_training_data(robot_code, version, data)
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
        agents[robot_code].update(dialogue_graph=data)
    else:
        _load_latest(robot_code)

    return {'status_code': 0}
