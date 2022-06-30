from config import global_config
from utils.define import ALGORITHM_CODE
from utils.funcs import post_rpc

EXTERNAL_XIAOYU_IP = global_config["external_xiaoyu_ip"]
EXTERNAL_XIAOYU_PORT = global_config["external_xiaoyu_port"]


def notify_training_complete(robot_code, version, msg="训练成功"):
    """向小语平台发送训练完成的请求

    Args:
        robot_code (str): 机器人唯一标识，ID
        version (str): 模型版本
        msg (str, optional): 模型训练状态，训练成功或者失败原因
    """
    url = "http://{}:{}/api/v1/algorithm/train/result".format(
        EXTERNAL_XIAOYU_IP, EXTERNAL_XIAOYU_PORT
    )
    data = {
        "algorithmCode": ALGORITHM_CODE,
        "robotId": robot_code,
        "version": version,
        "code": msg,
    }
    post_rpc(url, data, data_type="params")
