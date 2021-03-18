"""
此文件包含 faq 引擎请求帮助函数
"""
import json
import requests

from config import global_config
from utils.funcs import post_rpc

FAQ_ENGINE_ADDR = global_config['faq_engine_addr']


def faq_update(robot_id, data):
    """添加或者更新faq语料数据

    Args:
        robot_id (str): 机器人的唯一标识。
        data (list): 需要存储的问题数据。

    Return:
        response (dict): faq服务器返回的信息

    Examples:
        >>> robot_id = "doctest_id"
        >>> data = [
        ...    {
        ...        "faq_id": "id1",
        ...        "title": "苹果手机多少钱",
        ...        "similar_questions": [
        ...            "Apple手机多少钱",
        ...            "iphone多少钱"
        ...        ],
        ...        "related_quesions": [
        ...            "ipad多少钱",
        ...            "iwatch多少钱"
        ...        ],
        ...        "key_words": [
        ...            "苹果",
        ...            "Apple",
        ...            "iphone"
        ...        ],
        ...        "effective_time": "2020-12-31",
        ...        "tags": [
        ...            "手机",
        ...            "电子产品"
        ...        ],
        ...        "answer": "5400元",
        ...        "catagory": "电子产品价格"
        ...    }
        ... ]
        >>> faq_update(robot_id, data)
        {'status_code': 0}
    """
    url = "http://{}/robot_manager/single/add_items".format(FAQ_ENGINE_ADDR)

    documents = []
    for item in data:
        doc = {
            "answer": json.dumps(item, ensure_ascii=False),
            "question": item["title"],
            "id": item["faq_id"],
            "answer_id": item["faq_id"]
        }
        documents.append(doc)

    request_data = {
        "documents": documents,
        "robot_id": robot_id
    }
    return post_rpc(url, request_data)


def faq_delete(robot_id, data):
    """删除faq引擎中的语料数据

    Args:
        robot_id (str):  机器人的唯一标识。
        data (dict): 请求参数，里面包含需要删除的语料id

    Examples:
        >>> robot_id = "doctest_id"
        >>> qids = {"faq_ids": ["id1"]}
        >>> faq_delete(robot_id, qids)
        {'status_code': 0}
    """
    url = "http://{}/robot_manager/single/delete_items".format(FAQ_ENGINE_ADDR)
    q_ids = data["faq_ids"]
    request_data = {
        "q_ids": q_ids,
        "robot_code": robot_id
    }
    return post_rpc(url, request_data)


def faq_delete_all(robot_id):
    """删除特定机器人的所有语料

    Args:
        robot_id (str): 机器人的唯一标识

    Examples:
        >>> robot_id = "doctest_id"
        >>> faq_delete_all(robot_id)
        {'status_code': 0}
    """
    url = "http://{}/robot_manager/single/delete_robot".format(FAQ_ENGINE_ADDR)
    request_data = {
        "robot_code": robot_id
    }
    return post_rpc(url, request_data)


def faq_ask(robot_id, question):
    """向faq引擎提问
    Args:
        robot_id (str): 机器人的唯一标识
        question (str): 向机器人提问的问题

    Examples:
        >>> robot_id = "doctest_id"
        >>> question = "你好"
        >>> answer = faq_ask(robot_id, question)
        >>> isinstance(answer, dict)
        True
    """
    url = "http://{}/robot_manager/single/ask".format(FAQ_ENGINE_ADDR)
    request_data = {
        "robot_code": robot_id,
        "question": question
    }
    response_data = post_rpc(url, request_data)

    if response_data["answer_type"] == -1:
        return {
            "faq_id": "unknown",
            "title": "",
            "similar_questions": [],
            "related_quesions": [],
            "key_words": [],
            "effective_time": "",
            "tags": [],
            "answer": response_data["answer"],
            "catagory": ""
        }
    else:
        return json.loads(response_data["answer"])