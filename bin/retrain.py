"""
重新训练指定机器人，指定版本的nlu模型
"""

import os
import json
from config import global_config

# 不提前加载机器人，只加载需要测试的机器人
global_config["_delay_loading_robot"] = True
from backend.nlu import train_robot

cwd = os.path.abspath(os.path.dirname(__file__))
params = json.load(open(os.path.join(cwd, "params.json")))

robot_code = params["robot_code"]
nlu_version = params["nlu_version"]

train_robot(robot_code, nlu_version)
