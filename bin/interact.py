"""
交互测试机器人对话情况
"""
import os
import json

import backend.manager as manager

cwd = os.path.abspath(os.path.dirname(__file__))
params = json.load(open(os.path.join(cwd, "params.json")))


data = manager.session_create(params["robot_code"], "user1", params["params"])
sessionId = data["sessionId"]
print("机器人说：{}".format(data["says"]))

while True:
    user_says = input("用户说：")
    data = manager.session_reply(params["robot_code"], sessionId, user_says)
    print("机器人说：{}".format(data["says"]))
