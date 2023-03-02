"""
Train nlu with python script
"""
import glob
import json
import os
import shutil
from collections import defaultdict
from os.path import basename, dirname, join
from typing import Dict, Optional, Union

from xiaoyu.utils.define import (
    NLU_MODEL_AVALIABLE,
    NLU_MODEL_TRAINING,
    NLU_MODEL_USING,
    OperationResult,
)

__all__ = [
    "train_robot",
    "delete_robot",
    "create_lock",
    "release_lock",
    "update_training_data",
    "get_using_model",
    "get_nlu_raw_data",
]


def _nlu_data_convert(raw_data):
    """解析小语机器人前端传过来的数据格式，处理成ai后台所用的数据格式

    Args:
        raw_data (dict): 小语机器人前端传过来的数据

    Return:
        data (dict): AI后台可用的数据格式
    """
    rasa_template = {
        "rasa_nlu_data": {"common_examples": []},
        "regex_features": defaultdict(list),
        "key_words": defaultdict(list),
        "intent_rules": defaultdict(list),
        "intent_id2name": {},
        "intent_id2code": {},
    }

    for item in raw_data:
        intent = item["intent"]
        entity_synonyms = item.get("entity_synonyms", {})
        entity_regx = item.get("entity_regx", {})

        # 解析intent相关
        for cur in intent:
            rasa_template["intent_id2name"][cur["intent_id"]] = cur["intent_name"]
            # 由于这里intent_code字段是后面加的，为了保持配置兼容性，这里如果没有这个字段，则用intent_name替代
            rasa_template["intent_id2code"][cur["intent_id"]] = cur.get("intent_code", cur["intent_name"])
            for example in cur["user_responses"]:
                example["intent"] = cur["intent_id"]
            rasa_template["rasa_nlu_data"]["common_examples"].extend(cur["user_responses"])

            # 解析意图规则
            rasa_template["intent_rules"][cur["intent_id"]].extend(cur["intent_rules"])

        # 解析关键词识别能力
        for key, value in entity_synonyms.items():
            rasa_template["key_words"][key].extend(value)

        # 解析正则表达式识别能力
        for key, value in entity_regx.items():
            rasa_template["regex_features"][key].extend(value)

    return rasa_template


def get_model_path(model_storage_folder: str, robot_code: str, version: Optional[str] = None) -> str:
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


def get_nlu_data_path(model_storage_folder, robot_code, version):
    """获取nlu训练数据的路径

    Args:
        robot_code (str): 机器人的唯一标识
        version (str): 模型的版本

    Returns:
        str: nlu训练数据文件所在的路径
    """
    return join(get_model_path(model_storage_folder, robot_code, version), "raw_training_data.json")


def get_nlu_raw_data(model_storage_folder, robot_code, version):
    """获取nlu模型的训练数据

    Args:
        robot_code (str): 机器人的唯一标识
        version (str): 模型的版本

    Returns:
        dict: nlu训练数据的字典版本，如果指定的机器人nlu模型不存在，则返回None
    """
    nlu_data_path = get_nlu_data_path(model_storage_folder, robot_code, version)
    if not os.path.exists(nlu_data_path):
        return None
    with open(nlu_data_path, "r") as f:
        return json.load(f)


def create_lock(model_storage_folder, robot_code, version, status):
    """建立模型锁，防止模型错误加载

    Args:
        robot_code (str): 机器人的唯一标识
        version (str): 模型的版本
        status (str): NLU_MODEL_USING, NLU_MODEL_TRAINING其中之一
    """
    lockfile = join(get_model_path(model_storage_folder, robot_code, version), ".lock.{}".format(status))
    open(lockfile, "w").close()


def release_lock(model_storage_folder, robot_code, version="*", status="*"):
    """解除模型的所有锁

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 模型版本
        status (str): NLU_MODEL_USING, NLU_MODEL_TRAINING其中之一
    """
    for file in glob.glob(join(get_model_path(model_storage_folder, robot_code, version), ".lock.{}".format(status))):
        os.remove(file)


def get_model_status(model_storage_folder, robot_code, version):
    lockfiles = glob.glob(join(get_model_path(model_storage_folder, robot_code, version), ".lock.*"))
    for file in lockfiles:
        name = os.path.basename(file)
        suffix = name.split(".")[-1]
        return suffix

    return NLU_MODEL_AVALIABLE


def get_using_model(model_storage_folder: str, robot_code: Optional[str] = None) -> Optional[Union[str, Dict[str, str]]]:
    """获取某个机器人id下在使用的机器人，如果没有指定robot_code则返回所有在用的机器人

    Args:
        model_storage_folder (str): 模型存储的文件夹
        robot_code (str, optional): 机器人唯一标识. Defaults to None.

    Return:
        Optional[Union[str, Dict[str, str]]]: 如果指定了robot_code，则返回该机器人的模型版本号，如果没有指定robot_code，则返回所有在用的机器人的字典
    """
    if robot_code:
        using_model_paths = glob.glob(
            join(get_model_path(model_storage_folder, robot_code), "*", ".lock.{}".format(NLU_MODEL_USING))
        )
        if len(using_model_paths) > 0:
            return basename(os.path.dirname(using_model_paths[0]))
        else:
            return
    else:
        using_model_paths = glob.glob(join(model_storage_folder, "*/*", ".lock.{}".format(NLU_MODEL_USING)))
    using_model_paths = [os.path.dirname(item) for item in using_model_paths]
    return {basename(dirname(item)): basename(item) for item in using_model_paths}


def update_training_data(model_storage_folder, robot_code, version, nlu_data=None, _convert=True):
    """更新机器人的训练数据

    Args:
        robot_code (str): 机器人的唯一标识
        version (str, optional): 模型的版本
        nlu_data (str): nlu训练数据，json格式
        _convert (bool): 是否对传来的数据进行转换。
                (从前端直接传来的数据需要转换，push过来的数据不需要转换)
                default is False

    Return:
        utils.define.OperationResult: 操作结果对象
    """
    model_path = get_model_path(model_storage_folder, robot_code, version)
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    model_status = get_model_status(model_storage_folder, robot_code, version)
    if model_status == NLU_MODEL_TRAINING:
        return OperationResult(OperationResult.OPERATION_FAILURE, "模型正在训练中，请模型训练结束后再更新数据")

    nlu_data_path = get_nlu_data_path(model_storage_folder, robot_code, version)

    create_lock(model_storage_folder, robot_code, version, NLU_MODEL_TRAINING)
    if nlu_data:
        nlu_data = _nlu_data_convert(nlu_data) if _convert else nlu_data
        with open(nlu_data_path, "w") as f:
            json.dump(nlu_data, f, ensure_ascii=False)
    release_lock(model_storage_folder, robot_code, version)
    return OperationResult(OperationResult.OPERATION_SUCCESS, "训练数据更新成功")


def train_robot(model_storage_folder, robot_code, version):
    """训练多轮对话机器人的nlu模型

    Args:
        robot_code (str): 机器人的唯一标识
        version (str, optional): 模型的版本
    Return:
        utils.define.OperationResult: 操作结果对象
    """
    model_status = get_model_status(model_storage_folder, robot_code, version)
    if model_status == NLU_MODEL_TRAINING:
        return OperationResult(OperationResult.OPERATION_FAILURE, "模型正在训练中，请不要重复训练模型")

    create_lock(model_storage_folder, robot_code, version, NLU_MODEL_TRAINING)
    # TODO 训练模型

    release_lock(model_storage_folder, robot_code)  # 这里解除所有的锁
    create_lock(model_storage_folder, robot_code, version, NLU_MODEL_USING)
    return OperationResult(OperationResult.OPERATION_SUCCESS, "训练模型成功")


def delete_robot(model_storage_folder, robot_code, version="*", force=False):
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
            delete_path = get_model_path(model_storage_folder, robot_code)
        else:
            delete_path = get_model_path(model_storage_folder, robot_code, version)
        if os.path.exists(delete_path):
            shutil.rmtree(delete_path)
        return OperationResult(OperationResult.OPERATION_SUCCESS, "删除机器人成功")
    else:
        return OperationResult(OperationResult.OPERATION_FAILURE, "机器人模型正在使用或者正在训练中，请停用机器人或者等待机器人训练完毕")
