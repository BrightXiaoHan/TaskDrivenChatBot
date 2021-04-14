"""
重新训练指定机器人，指定版本的nlu模型
"""

import os
import json

from backend.nlu import train_robot

cwd = os.path.abspath(os.path.dirname(__file__))
params = json.load(open(os.path.join(cwd, "params.json")))

robot_code = params["robot_code"]
nlu_version = params["nlu_version"]

train_robot(robot_code, nlu_version)
