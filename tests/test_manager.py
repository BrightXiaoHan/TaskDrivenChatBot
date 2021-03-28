"""
测试对话流程
"""
import os
import json

import backend.manager as manager
from utils.define import MODEL_TYPE_NLU

robot_code = "_test"
version = "v0.1"
user_id = "user1"


def train_robot():

    cwd = os.path.dirname(os.path.abspath(__file__))
    # 训练机器人
    with open(os.path.join(cwd, "assets/faq_training_data.json")) as f:
        faq_data = json.load(f)
    manager.faq_train(robot_code, faq_data)

    with open(os.path.join(cwd, "assets/nlu_training_data.json")) as f:
        nlu_data = json.load(f)
    manager.nlu_train(robot_code, version, nlu_data)
    manager.nlu_train_sync(robot_code, version)

    with open(os.path.join(cwd, "assets/dialogue_graph.json")) as f:
        graph_data = json.load(f)
    manager.graph_train(robot_code, version, graph_data)

    # checkout here
    manager.checkout(robot_code, MODEL_TYPE_NLU, version)


def test_case_one():
    # 建立会话连接
    response = manager.session_create(robot_code, user_id, {
        "对话流程": "移车主流程", "号码归属地": "广州"})
    session_id = response["sessionId"]
    print("Robot: {}".format(response["says"]))

    user_says = "粤A23456"
    print("User: {}".format(user_says))
    response = manager.session_reply(robot_code, session_id, user_says)
    print("Robot: {}".format(response["says"]))

    user_says = "长沙神农大酒店"
    print("User: {}".format(user_says))
    response = manager.session_reply(robot_code, session_id, user_says)
    print("Robot: {}".format(response["says"]))


def main():
    train_robot()
    test_case_one()


if __name__ == '__main__':
    main()
