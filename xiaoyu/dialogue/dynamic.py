import json

from xiaoyu.config import global_config
from xiaoyu.utils.funcs import async_post_rpc

__all__ = ["dynamic_qa_train", "dynamic_intent_train", "dynamic_qa_delete", "dynamic_intent_delete"]

ROBOT_CODE = "dynamic_db"
ROBOT_CODE_INTENT = "dynamic_intent_db"
FIX_QUESTIONS = "fix_questions"
MAIN_QUESTION_PERSPECTIVE = "main_question"
SUB_QUESTION_PERSPECTIVE = "sub_question"
FAQ_ENGINE_ADDR = global_config["faq_engine_addr"]


async def dynamic_intent_train(data):
    """
    data数据格式示例
    [
        {
            "intent_id": "id1",
            "intent_code": "code",
            "intent_name": "表达苹果手机价格",
            "examples": ["苹果手机多少钱"],
            "intent_rules": [
                {
                    "regx": "${date}${city}[的]天气[预报|情况|状况]",
                    "strict": true
                },
                {
                    "regx": ".{0,3}${date}${city}[的]天气[预报|情况|状况].{0,3}",
                    "strict": true
                }
            ]
        }
    ]
    """
    url = "http://{}/robot_manager/single/add_items".format(FAQ_ENGINE_ADDR)
    documents = []
    for item in data:
        doc = {
            "answer": json.dumps(item, ensure_ascii=False),
            "perspective": item["intent_id"],
            "question": FIX_QUESTIONS,
            "id": item["intent_id"],
            "answer_id": item["intent_id"],
        }
        documents.append(doc)
    request_data = {"documents": documents, "robot_code": ROBOT_CODE_INTENT, "use_model": False}
    await async_post_rpc(url, request_data)
    return {"status_code": 0}


async def dynamic_qa_delete(data):
    """
    data 数据格式示例
    {
        "qids": [
            "id1",
            "id2"
        ]
    }
    """
    url = "http://{}/robot_manager/single/delete_items".format(FAQ_ENGINE_ADDR)
    q_ids = data["qids"]
    request_data = {"q_ids": q_ids, "robot_code": ROBOT_CODE}
    await async_post_rpc(url, request_data)
    return {"status_code": 0}


async def dynamic_qa_train(data):
    """
    data数据格式实例
    [
        {
        	"qid": "id1",
            "content": "苹果手机多少钱",
            "lib_ids": ["lib_id1", "lib_id2"]
            "tags": [
                "手机",
                "电子产品"
            ],
            "category_path": "1#2#3",
            "callback_words": ["请您回答我的问题，苹果手机多少钱呢"],
            "intent_ids": [
                "intent_id1",
                "intent_id2"
            ],
            "slots": [
                {
                    "key": "city",
                    "name": "城市",
                    "entity_key":"@识别能力key"
                }
            ],
            "parent_id": "id0",
            "child_ids": ["id2", "id3"],
            "parent_intent_id": "intent_id1"
        },
    ]
    """
    url = "http://{}/robot_manager/single/add_items".format(FAQ_ENGINE_ADDR)
    documents = []
    for item in data:
        perspective = item["lib_ids"]
        perspective.append(item["qid"])
        if "category_path" in item and item["category_path"]:
            perspective.extend(item["category_path"].split("#"))
        if "tags" in item and item["tags"]:
            perspective.extend(item["tags"])

        # 这里根据是否有parent_id来判断是否是子问题，如果是子问题，在perspective中加上相应的标识
        if "parent_id" in item and item["parent_id"] != "0":
            perspective.append(SUB_QUESTION_PERSPECTIVE)
        else:
            perspective.append(MAIN_QUESTION_PERSPECTIVE)
        doc = {
            "answer": json.dumps(item, ensure_ascii=False),
            "perspective": " ".join(perspective),
            "question": FIX_QUESTIONS,
            "id": item["qid"],
            "answer_id": item["qid"],
        }
        documents.append(doc)
    request_data = {"documents": documents, "robot_code": ROBOT_CODE, "use_model": False}
    await async_post_rpc(url, request_data)
    return {"status_code": 0}


async def dynamic_intent_delete(data):
    """
    data 数据格式示例
    {
        "intent_ids": [
            "id1",
            "id2"
        ]
    }
    """
    url = "http://{}/robot_manager/single/delete_items".format(FAQ_ENGINE_ADDR)
    q_ids = data["intent_ids"]
    request_data = {"q_ids": q_ids, "robot_code": ROBOT_CODE_INTENT}
    await async_post_rpc(url, request_data)
    return {"status_code": 0}
