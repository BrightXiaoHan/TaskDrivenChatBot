"""
测试将测试环境模型推送到正式环境
"""
from utils.funcs import post_rpc
from config import global_config

serve_port = global_config.get('serve_port')
robot_code = "_test"
version = "v0.1"


def test_push():

    data = {
        "robot_id": robot_code,
        "version": version
    }

    response = post_rpc(
        "http://127.0.0.1:{}/xiaoyu/push".format(serve_port), data)
    print(response)


if __name__ == "__main__":
    test_push()
