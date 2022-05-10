"""此文件包含 faq 引擎请求帮助函数."""
import copy
import json
import random

from config import global_config
from utils.define import (FAQ_DEFAULT_PERSPECTIVE, FAQ_TYPE_MULTIANSWER,
                          FAQ_TYPE_NONUSWER, UNK, get_faq_master_robot_id, get_faq_test_robot_id)
from utils.funcs import async_post_rpc

FAQ_ENGINE_ADDR = global_config["faq_engine_addr"]
MASTER_ADDR = global_config["master_addr"]
MAX_SIMILAR_QUESTIONS = 10  # 最大支持导入的相似问题个数

__all__ = [
    "faq_update",
    "faq_delete",
    "faq_delete_all",
    "faq_ask",
    "faq_push",
    "faq_chitchat_update",
    "faq_chitchat_ask",
]


def master_test_wrapper(func):
    async def wrapper(robot_id, *args, **kwargs):
        if not MASTER_ADDR:
            robot_id = get_faq_master_robot_id(robot_id)
        else:
            robot_id = get_faq_test_robot_id(robot_id)
        return await func(robot_id, *args, **kwargs)

    return wrapper


def _build_sim_id(origin_id: str, index: int) -> str:
    return origin_id + "_similar_{}".format(index)


@master_test_wrapper
async def faq_chitchat_update(robot_id, data):
    """
    添加或者更新闲聊数据.

    Args:
        data (dict): 闲聊数据.

    Examples:
        >>> data = [
        ...    {
        ...        "chatfest_id": "id1",
        ...        "theme": "苹果手机多少钱",
        ...        "similar_questions": [
        ...            "Apple手机多少钱",
        ...            "iphone多少钱"
        ...        ],
        ...        "answer": ["5400元", "五千四百元"],
        ...        "catagory": "电子产品价格"
        ...    }
        ... ]
    """
    url = "http://{}/robot_manager/single/add_items".format(FAQ_ENGINE_ADDR)

    documents = []
    for item in data:
        doc = {
            "answer": json.dumps(item, ensure_ascii=False),
            "perspective": FAQ_DEFAULT_PERSPECTIVE,
            "question": item["theme"],
            "id": item["chatfest_id"],
            "answer_id": item["chatfest_id"],
        }
        documents.append(doc)
        for i, sim_q in enumerate(item.get("similar_questions", [])):
            if i >= MAX_SIMILAR_QUESTIONS:
                break
            curdoc = copy.deepcopy(doc)
            curdoc["question"] = sim_q
            curdoc["id"] = _build_sim_id(curdoc["id"], i)
            documents.append(curdoc)

    request_data = {"documents": documents, "robot_code": robot_id}
    return await async_post_rpc(url, request_data)


@master_test_wrapper
async def faq_update(robot_id, data):
    """添加或者更新faq语料数据.

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
        perspective = item.get("perspective", "")  # 闲聊环节没有视角这个字段，忽略
        doc = {
            "answer": json.dumps(item, ensure_ascii=False),
            "perspective": perspective if perspective else FAQ_DEFAULT_PERSPECTIVE,
            "question": item["title"],
            "id": item["faq_id"],
            "answer_id": item["faq_id"],
        }
        documents.append(doc)
        for i, sim_q in enumerate(item.get("similar_questions", [])):
            if i >= MAX_SIMILAR_QUESTIONS:
                break
            curdoc = copy.deepcopy(doc)
            curdoc["question"] = sim_q
            curdoc["id"] = _build_sim_id(curdoc["id"], i)
            documents.append(curdoc)

    request_data = {"documents": documents, "robot_code": robot_id}
    return await async_post_rpc(url, request_data)


@master_test_wrapper
async def faq_delete(robot_id, data):
    """删除faq引擎中的语料数据.

    Args:
        robot_id (str):  机器人的唯一标识。
        data (dict): 请求参数，里面包含需要删除的语料id

    Examples:
        >>> robot_id = "doctest_id"
        >>> qids = {"faq_ids": ["id1"]}
        >>> faq_delete(robot_id, qids)
        {'status_code': 0}
    """
    # TODO 这里后续要考虑如何删除similar questions
    url = "http://{}/robot_manager/single/delete_items".format(FAQ_ENGINE_ADDR)
    q_ids = data["faq_ids"]
    if isinstance(q_ids, str):
        q_ids = [q_ids]

    # TODO 由于存储问题时默认会存储相似问题，这里需要把原问题关联的相似问题删除
    # 这里处理方式有点打补丁的意思
    all_ids = []
    for qid in q_ids:
        all_ids.extend([_build_sim_id(qid, i) for i in range(MAX_SIMILAR_QUESTIONS)])
    q_ids.extend(all_ids)

    request_data = {"q_ids": q_ids, "robot_code": robot_id}
    return await async_post_rpc(url, request_data)


@master_test_wrapper
async def faq_delete_all(robot_id):
    """删除特定机器人的所有语料.

    Args:
        robot_id (str): 机器人的唯一标识

    Examples:
        >>> robot_id = "doctest_id"
        >>> faq_delete_all(robot_id)
        {'status_code': 0}
    """
    url = "http://{}/robot_manager/single/delete_robot".format(FAQ_ENGINE_ADDR)
    request_data = {"robot_code": robot_id}
    return await async_post_rpc(url, request_data)


async def faq_push(robot_id):
    """复制faq节点index."""
    if not MASTER_ADDR:
        return {"status_code": 0}
    target_robot_id = get_faq_master_robot_id(robot_id)
    url = "http://{}/robot_manager/single/copy".format(FAQ_ENGINE_ADDR)
    request_data = {"robot_code": robot_id, "target_robot_code": target_robot_id}
    return await async_post_rpc(url, request_data)


@master_test_wrapper
async def faq_chitchat_ask(robot_id, question):
    """闲聊问答.

    Args:
        question (str): 问题

    Returns:
        dict: 闲聊问答结果

    Examples:
        >>> question = "苹果手机多少钱"
        >>> faq_chitchat_ask(question)
        {'status_code': 0, 'data': {'answer': '5400元', 'faq_id': 'id1', 'title': '苹果手机多少钱'}}
    """
    url = "http://{}/robot_manager/single/ask".format(FAQ_ENGINE_ADDR)
    request_data = {"question": question, "robot_code": robot_id}
    response_data = await async_post_rpc(url, request_data)
    response_data = response_data["data"]

    if response_data["answer_type"] == FAQ_TYPE_NONUSWER:
        return UNK
    elif response_data["answer_type"] == FAQ_TYPE_MULTIANSWER:
        answer_data = json.loads(response_data["answer"][0])
    else:
        answer_data = json.loads(response_data["answer"])

    return random.choice(answer_data["answers"])


@master_test_wrapper
async def faq_ask(
    robot_id,
    question,
    faq_params={
        "recommend_num": 5,
        "perspective": FAQ_DEFAULT_PERSPECTIVE,
        "dialogue_type": "text",
    },
):
    """
    向faq引擎提问.

    Args:
        robot_id (str): 机器人的唯一标识
        question (str): 向机器人提问的问题
        raw (bool, optional): 返回faq引擎的原始数据，还是返回解析后的答案数据。Default is False
        faq_params (int, optional): faq相关参数
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
        "question": question,
    }
    request_data.update(faq_params)
    response_data = await async_post_rpc(url, request_data)
    print(response_data)

    response_data = response_data["data"]

    if response_data["answer_type"] == FAQ_TYPE_NONUSWER:
        answer_data = {
            "faq_id": UNK,
            "title": "",
            "similar_questions": [],
            "related_quesions": [],
            "key_words": [],
            "effective_time": "",
            "tags": [],
            "answer": response_data["answer"],
            "catagory": "",
        }
    elif response_data["answer_type"] == FAQ_TYPE_MULTIANSWER:

        # 这里由于语音版本的faq需要播报可供选择的问题，这里对于不同的对话类型做不同的处理
        if faq_params["dialogue_type"] == "text":
            # text模式下直接返回相似度最高的问题
            answer_data = json.loads(response_data["answer"][0])
            response_data["confidence"] = response_data["confidence"][0]
        else:
            answer = "匹配到了多个相关问题，您想问的是哪一个呢？\n{}".format(
                "\n".join(response_data["match_questions"])
            )
            answer_data = {
                "faq_id": UNK,
                "title": "",
                "similar_questions": [],
                "related_quesions": [],
                "key_words": [],
                "effective_time": "",
                "tags": [],
                "answer": answer,
                "catagory": "",
            }
    else:  # FAQ_TYPE_SINGLEANSWER
        answer_data = json.loads(response_data["answer"])
    # 相关问题加推荐问题的总数为指定数量
    related_questions = answer_data.get("related_questions", [])
    rec_num = faq_params["recommend_num"] - len(related_questions)
    answer_data["recommendQuestions"] = response_data.get("recommendQuestions", [])[
        : rec_num + 1
    ]
    answer_data["confidence"] = response_data.get("confidence", 0)
    answer_data["hotQuestions"] = response_data.get("hotQuestions", [])
    answer_data["recommendScores"] = response_data.get("recommendScores", [])
    answer_data["reply_mode"] = response_data.get("reply_mode", "1")
    answer_data["sms_content"] = response_data.get("sms_content", "")
    answer_data["understanding"] = "3" if answer_data.get("faq_id", UNK) == UNK else "0"
    return answer_data
