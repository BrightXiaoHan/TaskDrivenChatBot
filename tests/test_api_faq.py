"""
测试faq相关api，启动服务后可以进行该测试·
"""
import time
from config import global_config
from utils.funcs import post_rpc
from utils.define import UNK

SERVE_PORT = global_config["serve_port"]
TEST_FAQ_DATA = [
    {
        "faq_id": "id1",
        "title": "苹果手机多少钱",
        "similar_questions": [
            "Apple手机多少钱",
            "iphone多少钱"
        ],
        "related_quesions": [
            "ipad多少钱",
            "iwatch多少钱"
        ],
        "key_words": [
            "苹果",
            "Apple",
            "iphone"
        ],
        "effective_time": "2020-12-31",
        "tags": [
            "手机",
            "电子产品"
        ],
        "answer": "5400元",
        "catagory": "电子产品价格"
    }
]
URL = "http://127.0.0.1:{}/xiaoyu/faq".format(SERVE_PORT)
TEST_ROBOT_ID = "test_faq_api_id"


def test_method_add():
    requests_data = {
        "robot_id": TEST_ROBOT_ID,
        "method": "add",
        "data": TEST_FAQ_DATA
    }
    response_data = post_rpc(URL, requests_data)
    assert response_data["code"] == 200


def test_method_update():
    faq_data = TEST_FAQ_DATA.copy()
    requests_data = {
        "robot_id": TEST_ROBOT_ID,
        "method": "update",
        "data": faq_data
    }
    response_data = post_rpc(URL, requests_data)
    assert response_data["code"] == 200


def test_method_delete():
    request_data = {
        "robot_id": TEST_ROBOT_ID,
        "method": "delete",
        "data": {
            "faq_ids": [TEST_FAQ_DATA[0]["faq_id"]]
        }
    }
    response_data = post_rpc(URL, request_data)
    assert response_data["code"] == 200

    request_data = {
        "robot_id": TEST_ROBOT_ID,
        "method": "ask",
        "data": {
            "question": "Apple手机多少钱"
        }
    }
    response_data = post_rpc(URL, request_data)
    assert response_data["data"]["faq_id"] == UNK

def test_method_ask():
    request_data = {
        "robot_id": TEST_ROBOT_ID,
        "method": "ask",
        "data": {
            "question": "苹果手机多少钱"
        }
    }
    response_data = post_rpc(URL, request_data)
    assert response_data["code"] == 200


if __name__ == "__main__":
    test_method_add()
    test_method_update()
    # sleep 10 second to wait anyq ready
    time.sleep(10)
    test_method_ask()
    test_method_delete()
