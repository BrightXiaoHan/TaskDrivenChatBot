"""
Train nlu with python script
"""
import os
import json
import glob
import shutil

from os.path import join, basename, dirname
from collections import defaultdict

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
           "release_lock", "update_training_data", "get_using_model"]


def _nlu_data_convert(raw_data):
    """解析小语机器人前端传过来的数据格式，处理成ai后台所用的数据格式

    Args:
        raw_data (dict): 小语机器人前端传过来的数据

    Return:
        data (dict): AI后台可用的数据格式
    """
    rasa_template = {
        "rasa_nlu_data": {
            "common_examples": []
        },
        "regex_features": defaultdict(list),
        "key_words": defaultdict(list),
        "intent_rules": defaultdict(list)
    }

    for item in raw_data:
        intent = item["intent"]
        entity_synonyms = item.get("entity_synonyms", {})
        entity_regx = item.get("entity_regx", {})

        # 解析intent相关
        for cur in intent:
            for example in cur["user_responses"]:
                example["intent"] = cur["intent_id"]
            rasa_template["rasa_nlu_data"]["common_examples"].extend(
                cur["user_responses"])

            # 解析意图规则
            rasa_template["intent_rules"][cur["intent_id"]].extend(
                cur["intent_rules"])

        # 解析关键词识别能力
        for key, value in entity_synonyms.items():
            rasa_template["key_words"][key].extend(value)

        # 解析正则表达式识别能力
        for key, value in entity_regx.items():
            rasa_template["regex_features"][key].extend(value)

        return rasa_template


def get_model_path(robot_code, version=None):
    """获取nlu模型存放的路径

    Args:
        robot_code (str): 机器人的唯一标识
        version (str): 模型的版本

    Returns:
        str: 模型所在文件夹的路径
    """
    if version:
        return join(model_storage_folder, robot_code, version)
    else:
        return join(model_storage_folder, robot_code)


def get_nlu_data_path(robot_code, version):
    """获取nlu训练数据的路径

    Args:
        robot_code (str): 机器人的唯一标识
        version (str): 模型的版本

    Returns:
        str: nlu训练数据文件所在的路径
    """
    return join(get_model_path(robot_code, version), "raw_training_data.json")


def create_lock(robot_code, version, status):
    """建立模型锁，防止模型错误加载

    Args:
        robot_code (str): 机器人的唯一标识
        version (str): 模型的版本
        status (str): NLU_MODEL_USING, NLU_MODEL_TRAINING其中之一
    """
    lockfile = join(get_model_path(
        robot_code, version), ".lock.{}".format(status))
    open(lockfile, "w").close()


def release_lock(robot_code, version="*", status="*"):
    """解除模型的所有锁

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 模型版本
        status (str): NLU_MODEL_USING, NLU_MODEL_TRAINING其中之一
    """
    for file in glob.glob(join(get_model_path(robot_code, version),
                               ".lock.{}".format(status))):
        os.remove(file)


def get_model_status(robot_code, version):
    lockfiles = glob.glob(join(get_model_path(robot_code, version), ".lock.*"))
    for file in lockfiles:
        name = os.path.basename(file)
        suffix = name.split(".")[-1]
        return suffix

    return NLU_MODEL_AVALIABLE


def get_using_model(robot_code=None):
    """获取某个机器人id下在使用的机器人，如果没有指定robot_code则返回所有在用的机器人

    Args:
        robot_code (str, optional): 机器人唯一标识. Defaults to None.

    Return:
        dict: key为robot_code，value为version
    """
    if robot_code:
        using_model_paths = glob.glob(
            join(get_model_path(robot_code), "*", ".lock.{}".format(NLU_MODEL_USING)))
        assert len(using_model_paths) == 1
        return basename(os.path.dirname(using_model_paths[0]))

    else:
        using_model_paths = glob.glob(
            join(model_storage_folder, "*/*", ".lock.{}".format(NLU_MODEL_USING)))

    using_model_paths = [os.path.dirname(item) for item in using_model_paths]

    return {basename(dirname(item)): basename(item) for item in using_model_paths}


def update_training_data(robot_code, version, nlu_data=None):
    """更新机器人的训练数据

    Args:
        robot_code (str): 机器人的唯一标识
        version (str, optional): 模型的版本
        nlu_data (str): nlu训练数据，json格式

    Return:
        utils.define.OperationResult: 操作结果对象
    """
    model_path = get_model_path(robot_code, version)
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    model_status = get_model_status(robot_code, version)
    if model_status == NLU_MODEL_TRAINING:
        return OperationResult(OperationResult.OPERATION_FAILURE,
                               "模型正在训练中，请模型训练结束后再更新数据")

    nlu_data_path = get_nlu_data_path(robot_code, version)

    create_lock(robot_code, version, NLU_MODEL_TRAINING)
    if nlu_data:
        nlu_data = _nlu_data_convert(nlu_data)
        with open(nlu_data_path, "w") as f:
            json.dump(nlu_data, f, ensure_ascii=False)
    release_lock(robot_code, version)
    return OperationResult(OperationResult.OPERATION_SUCCESS, "训练数据更新成功")


def train_robot(robot_code, version):
    """训练多轮对话机器人的nlu模型

    Args:
        robot_code (str): 机器人的唯一标识
        version (str, optional): 模型的版本
    Return:
        utils.define.OperationResult: 操作结果对象
    """
    model_status = get_model_status(robot_code, version)
    if model_status == NLU_MODEL_TRAINING:
        return OperationResult(OperationResult.OPERATION_FAILURE,
                               "模型正在训练中，请不要重复训练模型")

    create_lock(robot_code, version, NLU_MODEL_TRAINING)

    # 这里天坑，为了解决rasa训练数据的问题，这里代码不要动
    ##########################################################
    nlu_data = get_nlu_data_path(robot_code, version)
    with open(nlu_data) as f:
        data = json.load(f)
    data.pop("regex_features")
    data.pop("key_words")
    data.pop("intent_rules")

    nlu_data = join(dirname(nlu_data), "training_data.json")
    with open(nlu_data, "w") as f:
        json.dump(data, f, ensure_ascii=False)
    ##########################################################

    nlu_config = join(source_root, "assets/config_jieba_mitie_sklean.yml")
    training_data = load_data(nlu_data)
    trainer = Trainer(config.load(nlu_config))
    trainer.train(training_data)
    trainer.persist(model_storage_folder,
                    project_name=robot_code, fixed_model_name=version)
    release_lock(robot_code, version)
    return OperationResult(OperationResult.OPERATION_SUCCESS, "训练模型成功")


def delete_robot(robot_code, version="*", force=False):
    """删除模型

    Args:
        robot_code (str): 机器人标识
        version (str, optional): 模型版本号。Default is "*"，删除所有模型
        force (bool, optional): 是否强制删除。Default is False

    Return:
        utils.define.OperationResult: 操作结果对象
    """
    if NLU_MODEL_AVALIABLE == get_model_status(robot_code, "*") or force:
        if version == "*":
            delete_path = get_model_path(robot_code)
        else:
            delete_path = get_model_path(robot_code, version)
        if os.path.exists(delete_path):
            shutil.rmtree(delete_path)
        return OperationResult(OperationResult.OPERATION_SUCCESS, "删除机器人成功")
    else:
        return OperationResult(OperationResult.OPERATION_FAILURE,
                               "机器人模型正在使用或者正在训练中，请停用机器人或者等待机器人训练完毕")
