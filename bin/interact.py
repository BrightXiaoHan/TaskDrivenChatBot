"""
交互测试机器人对话情况
"""
import argparse
import asyncio
import os
import json
from pprint import pprint
from config import global_config

# 不提前加载机器人，只加载需要测试的机器人
global_config["_delay_loading_robot"] = True

from utils.define import MODEL_TYPE_NLU, MODEL_TYPE_DIALOGUE
import backend.manager as manager

# 加载参数
cwd = os.path.abspath(os.path.dirname(__file__))
params = json.load(open(os.path.join(cwd, "params.json")))

# nlu version 默认使用最新的，这里不再切换
# manager.checkout(params["robot_code"], MODEL_TYPE_NLU, params["nlu_version"])
try:
    manager.checkout(params["robot_code"], MODEL_TYPE_DIALOGUE,
                    params["dialogue_version"])
except Exception:
    print("加载指定的机器人多轮模型错误，下面的调用将直接请求faq引擎")


async def run():
    sessionId = "test_session"
    user_says = input("用户说：")
    data = await manager.session_reply(params["robot_code"], sessionId,
                                    user_says, "user1", params["params"])
    print("机器人说：{}".format(data["says"]))

    data = None
    while True:
        user_says = input("用户说：")
        if user_says == "info":
            print(manager.agents[
                params["robot_code"]].user_store[sessionId]._latest_msg())
        elif user_says == "verbose":
            pprint(data)
        else:
            data = await manager.session_reply(params["robot_code"], sessionId,
                                        user_says)
            pprint(data)
            print("机器人说：{}".format(data["says"]))

if __name__ == "__main__":
    asyncio.run(run())
