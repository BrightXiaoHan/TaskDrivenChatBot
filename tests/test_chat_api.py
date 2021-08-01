import os
import time
import json
from utils.funcs import post_rpc
from config import global_config

serve_port = global_config.get('serve_port')
robot_code = "test_robot_id"
version = "v0.1"
user_id = "user1"
cwd = os.path.dirname(os.path.abspath(__file__))


def train_nlu():
    with open(os.path.join(cwd, "assets/nlu_training_data.json")) as f:
        nlu_data = json.load(f)
    # 训练nlu模型
    data = {
        "robot_id": robot_code,
        "method": "train",
        "version": version,
        "data": nlu_data
    }
    response = post_rpc(
        "http://127.0.0.1:{}/xiaoyu/multi/nlu".format(serve_port),
        data)
    print(response)


def train_dialogue():
    with open(os.path.join(cwd, "assets/dialogue_graph.json")) as f:
        graph_data = json.load(f)

    # 上传对话流程配置
    data = {
        "robot_id": robot_code,
        "method": "train",
        "version": version,
        "data": graph_data
    }
    response = post_rpc(
        "http://127.0.0.1:{}/xiaoyu/multi/graph".format(serve_port),
        data)
    print(response)


def test_chat():
    session_id = "test_chat_api"
    data = {
        "robotId": robot_code,
        "userCode": "user1",
        "sessionId": session_id,
        "params": {"归属地": "广州"}
    }
    response = post_rpc(
        "http://127.0.0.1:{}/api/v1/session/reply".format(serve_port),
        data
    )
    print(response)

    data = {
        "robotId": robot_code,
        "userCode": "user1",
        "sessionId": session_id,
        "userSays": "今天广州天气怎么样"

    }
    response = post_rpc(
        "http://127.0.0.1:{}/api/v1/session/reply".format(serve_port),
        data
    )
    print(response)


def test_system():
    # 删除机器人
    data = {
        "robot_id": robot_code
    }
    response = post_rpc("http://127.0.0.1:{}/xiaoyu/delete".format(serve_port),
                        data)
    print(response)


def main():
    train_nlu()
    time.sleep(60)
    train_dialogue()
    test_chat()
    test_system()


if __name__ == '__main__':
    main()
