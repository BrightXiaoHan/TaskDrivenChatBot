"""此文件包含 faq 引擎请求帮助函数."""
import copy
import json
from typing import Any, Dict, List

from xiaoyu.rpc.index import delete_documents, delete_robot, upload_documents
from xiaoyu.rpc.search import search
from xiaoyu.utils.define import (
    FAQ_DEFAULT_PERSPECTIVE,
    FAQ_TYPE_MULTIANSWER,
    FAQ_TYPE_NONUSWER,
    UNK,
    get_faq_master_robot_code,
    get_faq_test_robot_code,
)

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


def _handle_robot_code(robot_code: str, is_master: bool = False) -> str:
    if is_master:
        return get_faq_master_robot_code(robot_code)
    else:
        return get_faq_test_robot_code(robot_code)


def _build_sim_id(origin_id: str, index: int) -> str:
    return origin_id + "_similar_{}".format(index)


async def faq_update(robot_code: str, data: List[Dict[str, Any]], is_master=False) -> None:
    """添加或者更新faq语料数据.

    Args:
        robot_code (str): 机器人的唯一标识。
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
    robot_code = _handle_robot_code(robot_code, is_master)
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
    await upload_documents(robot_code, documents)


async def faq_delete(robot_code: str, faq_ids: List[str], is_master=False) -> None:
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
    robot_code = _handle_robot_code(robot_code, is_master)
    # TODO 由于存储问题时默认会存储相似问题，这里需要把原问题关联的相似问题删除
    # 这里处理方式有点打补丁的意思
    all_ids = []
    for qid in faq_ids:
        all_ids.extend([_build_sim_id(qid, i) for i in range(MAX_SIMILAR_QUESTIONS)])
    faq_ids.extend(all_ids)

    await delete_documents(robot_code, faq_ids)


async def faq_delete_all(robot_code: str, is_master: bool = False) -> None:
    """删除特定机器人的所有语料.

    Args:
        robot_id (str): 机器人的唯一标识

    Examples:
        >>> robot_id = "doctest_id"
        >>> faq_delete_all(robot_id)
    """
    robot_code = _handle_robot_code(robot_code, is_master)
    await delete_robot(robot_code)


async def faq_push(robot_code: str, is_master: bool = False) -> None:
    """复制faq节点index."""
    if is_master:
        return
    source_robot_code = get_faq_test_robot_id(robot_code)
    target_robot_id = get_faq_master_robot_id(robot_code)
    await copy(source_robot_code, target_robot_id)


async def faq_chitchat_ask(robot_code, question):
    """闲聊问答.

    Args:
        robot_code (str): 机器人的唯一标识。
        question (str): 问题

    Returns:
        dict: 闲聊问答结果

    """
    # TODO 接入百度闲聊回答
    return question


async def faq_ask(
    robot_code: str,
    question: str,
    faq_params: Dict[str, str] = {
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
    dialogue_type = faq_params.pop("dialogue_type", "text")
    response_data = await search(robot_code, question, **faq_params)

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
        if dialogue_type == "text":
            # text模式下直接返回相似度最高的问题
            answer_data = json.loads(response_data["answer"][0])
            response_data["confidence"] = response_data["confidence"][0]
        else:
            answer = "匹配到了多个相关问题，您想问的是哪一个呢？\n{}".format("\n".join(response_data["match_questions"]))
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
    answer_data["recommendQuestions"] = response_data.get("recommendQuestions", [])[: rec_num + 1]
    answer_data["confidence"] = response_data.get("confidence", 0)
    answer_data["hotQuestions"] = response_data.get("hotQuestions", [])
    answer_data["recommendScores"] = response_data.get("recommendScores", [])
    answer_data["reply_mode"] = response_data.get("reply_mode", "1")
    answer_data["sms_content"] = response_data.get("sms_content", "")
    answer_data["understanding"] = "3" if answer_data.get("faq_id", UNK) == UNK else "0"
    return answer_data
