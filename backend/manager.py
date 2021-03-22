"""
机器人资源、对话管理
"""
from backend.nlu.interpreter import load_all_using_interpreters
from backend.dialogue.graph_parser import get_graph_data
from backend.dialogue.agent import Agent

robots_interpreters = load_all_using_interpreters()
robots_graph = {robot_code: get_graph_data(robot_code)
                for robot_code in robots_interpreters}

# 获取所有可用的robot_code
robot_codes = [robot_code for robot_code,
               graph in robots_graph.items() if graph]

agents = {robot_code: Agent(
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
    return {
        "sessionId": None,
        "type": "2",
        "responseTime": None,
        "says": None
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

    return None


def delete(robot_code):
    """删除整个机器人

    Args:
        robot_code (str): 机器人唯一标识

    Returns:
        [type]: [description]
    """
    return None


def push(robot_code, type, version):
    """将某个版本的模型推送到正式环境

    Args:
        robot_code (str): 机器人唯一标识
        type (str): 类型，参见utils.define.MODEL_TYPE_*
        version (str): 对应模型或配置的版本
    """
    return None


def checkout(robot_code, type, version):
    """将模型或配置回退到某个版本

    Args:
        robot_code (str): 机器人唯一标识
        type (str): 类型，参见utils.define.MODEL_TYPE_*
        version (str): 对应模型或配置的版本
    """
    return None


def nlu(robot_code, version, data):
    """训练nlu模型，这里nlu模型因为是异步训练，无法及时推送到使用版本。
       训练请求将发送到训练进程进行训练，训练完毕后会通知后台训练完毕，
       并使用checkout方法，将nlu模型切换到新训练的版本

    Args:
        robot_code (str): 机器人唯一标识
        version (str): nlu数据版本号
        data (dict): 前端配置生成的nlu训练数据
    """
    return None


def graph(robot_code, version, data):
    """[summary]

    Args:
        robot_code (str): 机器人唯一标识
        version (str): nlu数据版本号
        data (dict): 前端配置生成的对话流程配置数据
    """
