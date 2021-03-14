"""
Train nlu with python script
"""
import os
import glob
import shutil

from rasa_nlu.training_data import load_data
from rasa_nlu.model import Trainer
from rasa_nlu import config

from config import global_config
from utils.define import (NLU_MODEL_USING,
                          NLU_MODEL_TRAINING,
                          NLU_MODEL_AVALIABLE,
                          OperationResult)

model_storage_folder = global_config["model_storage_folder"]
source_root = global_config["source_root"]

__all__ = ["train_robot", "delete_robot", "create_lock",
           "release_lock", "update_training_data"]


def create_lock(robot_code, version, status):
    """建立模型锁，防止模型错误加载

    Args:
        robot_code (str): 机器人的唯一标识
        version (str): 模型的版本
        status (str): NLU_MODEL_USING, NLU_MODEL_TRAINING其中之一
    """
    lockfile = os.path.join(model_storage_folder,
                            robot_code, version,
                            ".lock.{}".format(status))

    open(lockfile, "w").close()


def release_lock(robot_code, version):
    """解除模型的所有锁

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 模型版本
    """
    for file in glob.glob(os.path.join(model_storage_folder,
                                       robot_code, version, ".lock.*")):
        os.remove(file)


def get_model_status(robot_code, version):
    lockfiles = glob.glob(os.path.join(
        model_storage_folder, robot_code, version, ".lock.*"))
    for file in lockfiles:
        name = os.path.basename(file)
        suffix = name.split(".")[-1]
        return suffix

    return NLU_MODEL_AVALIABLE


def update_training_data(robot_code, version, nlu_data=None, dialogue_graph=None):
    """更新机器人的训练数据

    Args:
        robot_code (str): 机器人的唯一标识
        version (str, optional): 模型的版本
        nlu_data (str): nlu训练数据，json给是
        dialogue_graph (str): 对话流程配置数据，json格式

    Return:
        utils.define.OperationResult: 操作结果对象
    """
    model_path = os.path.join(model_storage_folder, robot_code, version)
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    model_status = get_model_status(robot_code, version)
    if model_status == NLU_MODEL_USING:
        return OperationResult(OperationResult.OPERATION_FAILURE,
                               "模型正在使用中，请停用模型后再更新训练数据")
    elif model_status == NLU_MODEL_TRAINING:
        return OperationResult(OperationResult.OPERATION_FAILURE,
                               "模型正在训练中，请模型训练结束后再更新数据")

    nlu_data_path = os.path.join(model_path, "training_data.json")
    dialogue_graph_path = os.path.join(model_path, "dialogue_graph.json")

    create_lock(robot_code, version, NLU_MODEL_TRAINING)
    if nlu_data:
        with open(nlu_data_path, "w") as f:
            f.write(nlu_data)
    if dialogue_graph:
        with open(dialogue_graph_path, "w") as f:
            f.write(dialogue_graph)
    release_lock(robot_code, version)
    return OperationResult(OperationResult.OPERATION_SUCCESS, "训练数据更新成功")


def train_robot(robot_code, version, _nlu_data=None):
    """训练多轮对话机器人的nlu模型

    Args:
        robot_code (str): 机器人的唯一标识
        version (str, optional): 模型的版本
        _nlu_data (str, optional): 用于测试脚本指定nlu训练数据的位置。
            其他场景不要使用该参数。Default is None
    Return:
        utils.define.OperationResult: 操作结果对象
    """
    model_status = get_model_status(robot_code, version)
    if model_status == NLU_MODEL_USING:
        return OperationResult(OperationResult.OPERATION_FAILURE,
                               "模型正在使用中，训练模型失败")
    elif model_status == NLU_MODEL_TRAINING:
        return OperationResult(OperationResult.OPERATION_FAILURE,
                               "模型正在训练中，请不要重复训练模型")

    create_lock(robot_code, version, NLU_MODEL_TRAINING)
    if _nlu_data:
        nlu_data = _nlu_data
    else:
        nlu_data = os.path.join(model_storage_folder,
                                robot_code, version, "training_data.json")
    nlu_config = os.path.join(
        source_root, "assets/config_jieba_mitie_sklean.yml")
    training_data = load_data(nlu_data)
    trainer = Trainer(config.load(nlu_config))
    trainer.train(training_data)
    trainer.persist(model_storage_folder,
                    project_name=robot_code, fixed_model_name=version)
    release_lock(robot_code, version)
    return OperationResult(OperationResult.OPERATION_SUCCESS, "训练模型成功")


def delete_robot(robot_code, version="*"):
    """删除模型

    Args:
        robot_code (str): 机器人标识
        version (str, optional): 模型版本号。Default is "*"，删除所有模型

    Return:
        utils.define.OperationResult: 操作结果对象
    """
    if NLU_MODEL_AVALIABLE == get_model_status(robot_code, "*"):
        if version == "*":
            delete_path = os.path.join(model_storage_folder, robot_code)
        else:
            delete_path = os.path.join(
                model_storage_folder, robot_code, version)
        if os.path.exists(delete_path):
            shutil.rmtree(delete_path)
        return OperationResult(OperationResult.OPERATION_SUCCESS, "删除机器人成功")
    else:
        return OperationResult(OperationResult.OPERATION_FAILURE,
                               "机器人模型正在使用或者正在训练中，请停用机器人或者等待机器人训练完毕")
