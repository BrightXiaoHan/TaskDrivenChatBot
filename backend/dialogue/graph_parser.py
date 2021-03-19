"""
对话流程配置数据解析模块
"""
import json
import os
from os.path import join, dirname, exists

from config import global_config
from utils.define import OperationResult

graph_storage_folder = global_config["graph_storage_folder"]


def get_graph_path(robot_code, version):
    """
    获得机器人指定版本的对话流程配置文件路径
    """
    return join(graph_storage_folder, robot_code, version+".json")


def get_graph_data(robot_code, version):
    """
    获取指定机器人，指定版本的模型
    """
    graph_path = get_graph_path(robot_code, version)
    try:
        with open(graph_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        pass

    return data


def update_dialogue_graph(robot_code, version, data):
    """更新对话流程配置数据

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 流程配置版本
        data (dict): 对话流程配置字典

    Returns:
        utils.define.OperationResult: 操作结果
    """
    graph_path = get_graph_path(robot_code, version)
    folder = dirname(graph_path)

    if not exists(folder):
        os.makedirs(folder)

    with open(get_graph_path, "w") as f:
        json.dump(data, f, ensure_ascii=False)

    return OperationResult(OperationResult.OPERATION_SUCCESS, "更新对话流程配置成功")
