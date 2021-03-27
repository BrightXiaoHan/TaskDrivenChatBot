"""
对话流程配置数据解析模块
"""
import json
import glob
import os
import shutil
from os.path import join, dirname, exists, basename

from config import global_config
from utils.define import OperationResult, MODEL_TYPE_DIALOGUE
from utils.exceptions import NoAvaliableModelException

graph_storage_folder = global_config["graph_storage_folder"]

__all__ = ["delete_robot", "update_dialogue_graph", "checkout"]


def get_graph_path(robot_code, graph_id, version="latest"):
    """
    获得机器人指定版本的对话流程配置文件路径

    Args:
        robot_code (str): 机器人唯一标识
        graph_id (str): 每个机器人可以配置多个对话流程图，对话流程图id
        version (str, optional): Default is "latest".
                                 模型版本，当没有指定该参数时，返回当前正在使用的模型版本

    Return:
        str: 模型所在路径
    """
    return join(graph_storage_folder, robot_code, version, graph_id + ".json")


def get_graph_data(robot_code, graph_id, version="latest"):
    """
    获取指定机器人，指定版本的对话流程配置
    """
    graph_path = get_graph_path(robot_code, graph_id, version)
    try:
        with open(graph_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise NoAvaliableModelException(
            robot_code, version + "-" + graph_id, MODEL_TYPE_DIALOGUE)

    return data


def delete_robot(robot_code, version=None):
    """
    删除机器人某个特定版本的模型，或者删除整个机器人。
    """
    if version:
        delete_path = join(graph_storage_folder, robot_code, version)
    else:
        delete_path = join(graph_storage_folder, robot_code)

    if os.path.exists(delete_path):
        shutil.rmtree(delete_path)
    return OperationResult(OperationResult.OPERATION_SUCCESS,
                           "删除对话流程配置成功")


def update_dialogue_graph(robot_code, version, graph_id, data):
    """更新对话流程配置数据

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 流程配置版本
        graph_id (str): 每个机器人可以配置多个对话流程图，对话流程图id
        data (dict): 对话流程配置字典

    Returns:
        utils.define.OperationResult: 操作结果
    """
    graph_path = get_graph_path(robot_code, graph_id, version)
    folder = dirname(graph_path)

    if not exists(folder):
        os.makedirs(folder)

    with open(graph_path, "w") as f:
        json.dump(data, f, ensure_ascii=False)

    # 将最后更新的模型置为最新的配置
    with open(get_graph_path(robot_code, graph_id), "w") as f:
        json.dump(data, f, ensure_ascii=False)

    return OperationResult(OperationResult.OPERATION_SUCCESS, "更新对话流程配置成功")


def checkout(robot_code, version):
    """切换到某个版本的对话流程配置

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 流程配置版本号

    Return:
        data: 配置
    """
    graph_paths = glob.glob(
        join(graph_storage_folder, robot_code, version, "*.json"))

    all_data = {}

    for path in graph_paths:
        graph_id = basename(path).split(".")[0]
        with open(path, "r") as f:
            data = json.load(f)

        # 将最后更新的模型置为最新的配置
        with open(get_graph_path(robot_code, graph_id), "w") as f:
            json.dump(data, f, ensure_ascii=False)
        all_data[graph_id] = data

    return all_data
