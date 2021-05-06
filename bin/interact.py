"""
交互测试机器人对话情况
"""
from utils.define import MODEL_TYPE_NLU, MODEL_TYPE_DIALOGUE
import backend.manager as manager
import os
import json
from pprint import pprint as print
from config import global_config

# 不提前加载机器人，只加载需要测试的机器人
global_config["_delay_loading_robot"] = True


# 加载参数
cwd = os.path.abspath(os.path.dirname(__file__))
params = json.load(open(os.path.join(cwd, "params.json")))

manager.checkout(params["robot_code"], MODEL_TYPE_NLU, params["nlu_version"])
manager.checkout(params["robot_code"], MODEL_TYPE_DIALOGUE,
                 params["dialogue_version"])

data = manager.session_create(params["robot_code"], "user1", params["params"])
sessionId = data["sessionId"]
print("机器人说：{}".format(data["says"]))

data = None
while True:
    user_says = input("用户说：")
    if user_says == "info":
        print(manager.agents[
            params["robot_code"]].user_store[sessionId]._latest_msg())
    elif user_says == "verbose":
        print(data)
    else:
        data = manager.session_reply(params["robot_code"], sessionId,
                                     user_says)
        print("机器人说：{}".format(data["says"]))
