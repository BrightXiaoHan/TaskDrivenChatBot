"""
测试对话流程
"""
import os
import json
from config import global_config

# 不提前加载机器人，只加载需要测试的机器人
global_config["_delay_loading_robot"] = True

import backend.manager as manager
from utils.define import MODEL_TYPE_NLU

robot_code = "test_robot_id"
version = "v0.1"
user_id = "user1"
cwd = os.path.dirname(os.path.abspath(__file__))


def train_robot():

    # 训练机器人
    with open(os.path.join(cwd, "assets/faq_training_data.json")) as f:
        faq_data = json.load(f)

    with open(os.path.join(cwd, "assets/nlu_training_data.json")) as f:
        nlu_data = json.load(f)

    with open(os.path.join(cwd, "assets/dialogue_graph_two.json")) as f:
        graph_data_two = json.load(f)

    with open(os.path.join(cwd, "assets/dialogue_graph.json")) as f:
        graph_data_one = json.load(f)

    manager.faq_train(robot_code, faq_data)
    manager.graph_train(robot_code, version, graph_data_one)
    manager.graph_train(robot_code, version, graph_data_two)

    manager.nlu_train(robot_code, version, nlu_data)
    manager.nlu_train_sync(robot_code, version)

    # checkout here
    manager.checkout(robot_code, MODEL_TYPE_NLU, version)


def test_case_one():
    """
    测试移车完整顺利流程
    """
    # 建立会话连接
    params = {"对话流程": "移车主流程", "号码归属地": "广州"}
    session_id = "test_session_one"
    # 建立连接
    response = manager.session_reply(robot_code, session_id, "空消息", params=params)
    print("Robot: {}".format(response["says"]))

    says = [
        "粤A23456",
        "苹果手机多少钱",
        "是的",
        "长沙神农大酒店"
    ]

    for say in says:
        print("User: {}".format(say))
        response = manager.session_reply(robot_code, session_id, say)
        print("Robot: {}".format(response["says"]))


def test_case_two():
    """
    测试中途转人工
    """
    params = {"对话流程": "移车主流程", "归属地": "广州"}
    session_id = "test_case_two"

    # 建立会话连接
    response = manager.session_reply(robot_code, session_id, "空消息", params=params)
    print("Robot: {}".format(response["says"]))

    says = [
        "转人工"
    ]

    for say in says:
        print("User: {}".format(say))
        response = manager.session_reply(robot_code, session_id, say)
        print("Robot: {}".format(response["says"]))


def test_case_three():
    """
    测试用户说开头的流程
    """
    params = {"归属地": "广州"}
    session_id = "test_case_three"
    print("User: {}".format("今天天气怎么样"))
    response = manager.session_reply(robot_code, session_id, "今天天气怎么样", params=params)
    print("Robot: {}".format(response["says"]))
    says = [
        "广州",
        "重新询问",
        "今天天气怎么样",
        "广州",
        "再见",
        "苹果手机多少钱"
    ]

    for say in says:
        print("User: {}".format(say))
        response = manager.session_reply(robot_code, session_id, say)
        print("Robot: {}".format(response["says"]))


def main():
    train_robot()
    test_case_one()
    test_case_two()
    test_case_three()


if __name__ == '__main__':
    main()
