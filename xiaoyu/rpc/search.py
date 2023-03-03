import uuid
from itertools import chain
from typing import Any, Dict, List

import ngram
import numpy as np
from elasticsearch import AsyncElasticsearch, helpers
from more_itertools import take
from toolz import unique

from xiaoyu.utils.define import (
    FAQ_TYPE_MULTIANSWER,
    FAQ_TYPE_NONUSWER,
    FAQ_TYPE_SINGLEANSWER,
)
from xiaoyu_interface.call import semantic_index
from xiaoyu_interface.sentence_transformers import (
    SemanticIndexInputExample,
    SemanticIndexOutputExample,
)

es = AsyncElasticsearch("http://elastic:xiaoyu@localhost:19200")


def judge_answer(question: str, hits: List[Dict], threshold: float) -> List[Dict]:
    """
    判断候选的问题是否符合直接返回答案的条件

    Args:
        question (str): 待匹配的问题
        hits (List[Dict]): 语义匹配命中的问题
        threshold (float): 相似度的阈值

    Return
        List[Dict]: 可以作为答案的hit，没有任何命中时，返回None
    """

    def answer_filter(hit):
        if hit["_score"] - 1 <= threshold:
            return False

        if len(question) <= 5:
            ngram_sim = ngram.NGram.compare(question, hit["_source"]["question"], N=1)
            if ngram_sim < 0.5:
                return False

        return True

    hits = list(filter(answer_filter, hits))
    # 当搜索命中的数量为0时，直接返回None
    if not hits:
        return []
    elif len(hits) == 1:
        return hits[0:1]
    else:
        if hits[0]["_score"] - 1 >= 0.93:
            return hits[0:1]
        elif hits[0]["_score"] - hits[1]["_score"] > 0.15:
            return hits[0:1]
        else:
            return hits


async def query_minhash(text: str) -> str:
    """
    将用户的请求数据插入到es中，并返回minhash值

    Args:
        text (str): 用户的请求数据

    Return:
        str: minhash值
    """
    index_name = "internal_minhash"
    if not await es.indices.exists(index=index_name):
        es_index = {
            "mappings": {
                "properties": {
                    "question": {"type": "text", "copy_to": "minhash_value"},
                    "minhash_value": {
                        "type": "minhash",
                        "store": True,
                        "minhash_analyzer": "minhash_analyzer",
                    },
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "minhash_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["my_minhash"],
                        }
                    },
                    "filter": {"my_minhash": {"type": "minhash", "hash_count": 128}},
                },
            },
        }
        await es.indices.create(index=index_name, body=es_index)
    # 插入数据
    uid = uuid.uuid4().hex
    doc = {"_id": uid, "_index": index_name, "_source": {"question": text}}
    await helpers.async_bulk(es, [doc], refresh=True)
    # 获取minhash值
    res = await es.get(index=index_name, id=uid, stored_fields=["minhash_value"])
    # delete doc
    await es.delete(index=index_name, id=uid)
    return res["fields"]["minhash_value"][0]


async def search(
    robot_code: str,
    question: str,
    ans_threshold: float = 0.5,
    rcm_threshold: float = 0.4,
    recommend_num: int = 5,
    perspective: str = "",
    should_perspective: str = "",
    use_model: bool = True,  # 是否使用语义模型进行搜索,如果该字段为False,则使用关键字搜索
) -> Dict[str, Any]:
    response_json = {
        "answer": "",
        "match_questions": "",
        "answer_type": FAQ_TYPE_NONUSWER,
        "confidence": 0,
        "hotQuestions": [],
        "recommendQuestions": [],
        "recommendScores": [],
        "recommendAnswers": [],
    }
    if not await es.indices.exists(index=robot_code, ignore=[400, 404]):
        return response_json

    # 这里不知道如何外部计算，只能插入到elasticsearch中再查询删除
    minhash_value = await query_minhash(question)

    perspective = set(perspective.split(" "))
    should_perspective = set(should_perspective.split(" "))
    perspective_matcher = {
        "bool": {
            "must": [
                {"bool": {"must": [{"match_phrase": {"perspective": {"query": p}}} for p in perspective if p]}},  # 避免空字符串
                {
                    "bool": {
                        "should": [{"match_phrase": {"perspective": {"query": p}}} for p in should_perspective if p]  # 避免空字符串
                    }
                },
            ]
        }
    }

    if use_model:
        question_embedding: SemanticIndexOutputExample = semantic_index(SemanticIndexInputExample(sentences=question))
        sem_search = await es.search(
            index=robot_code,
            body={
                "query": {
                    "script_score": {
                        "query": perspective_matcher,
                        "script": {
                            # 这里余弦相似度加1是因为score的值不能小于0
                            "source": "cosineSimilarity(params.query_vector, 'question_vector') + 1",
                            "params": {"query_vector": question_embedding.embeddings},
                        },
                    }
                },
                "_source": ["question", "answer"],
            },
        )
        hits = sem_search["hits"]["hits"]
        hits = list(unique(hits, lambda x: x["_source"]["answer"]))
        answer = judge_answer(question, hits, ans_threshold)[:3]  # 这里欧工要求的，最多只取三个问题
    else:
        sem_search = await es.search(
            index=robot_code,
            body={
                "query": {"fuzzy": {"minhash_value": minhash_value}},
                "_source": ["question", "answer"],
            },
        )
        # 这里硬编码，强制设置score为阈值之上，防止被过滤掉
        for hit in sem_search["hits"]["hits"]:
            hit["_score"] = ans_threshold + 1
        hits = sem_search["hits"]["hits"]
        answer = hits[:3]  # 这里欧工要求的，最多只取三个问题

    if answer and len(answer) == 1:
        answer = answer[0]
        response_json["answer"] = answer["_source"]["answer"]
        response_json["match_questions"] = answer["_source"]["question"]
        response_json["confidence"] = answer["_score"] - 1
        response_json["answer_type"] = FAQ_TYPE_SINGLEANSWER
    elif answer and len(answer) > 1:
        response_json["answer"] = [item["_source"]["answer"] for item in answer]
        response_json["answer_type"] = FAQ_TYPE_MULTIANSWER
        response_json["match_questions"] = [item["_source"]["question"] for item in answer]
        response_json["confidence"] = [item["_score"] - 1 for item in answer]

    # 过滤掉答案相同的问题
    start = 1 if answer and len(answer) == 1 else 0
    hits = hits[start:]

    def _sim_search_filter(hit):
        if hit["_score"] - 1 < rcm_threshold:
            return False

        if len(hit["_source"]["question"]) <= 4 and ngram.NGram.compare(question, hit["_source"]["question"], N=1) == 0:
            return False

        return True

    hits = list(filter(_sim_search_filter, hits))

    # 如果没有语义匹配结果，则使用关键词匹配，加语义最相似问题
    if len(hits) < recommend_num and use_model:
        phrase_search = await es.search(
            index=robot_code,
            body={
                "query": {"fuzzy": {"minhash_value": minhash_value}},
                "_source": ["question", "answer"],
            },
        )
        search_hits = phrase_search["hits"]["hits"]
        # 关键词搜索得到的结果，置信度都置为推荐问题的阈值
        for hit in search_hits:
            hit["_score"] = rcm_threshold + 1

        hits = unique(chain(hits, search_hits), lambda x: x["_source"]["answer"])

    # 过滤掉与答案对应问题重复的问题
    hits = filter(lambda x: x["_source"]["answer"] != response_json["answer"], hits)
    if recommend_num > 0:
        hits = take(recommend_num, hits)

    for hit in hits:
        response_json["recommendQuestions"].append(hit["_source"]["question"])
        response_json["recommendAnswers"].append(hit["_source"]["answer"])
        response_json["recommendScores"].append(hit["_score"] - 1)
    return response_json


def intent_classify(question: str, intent_group: Dict[str, List[str]]) -> Dict[str, List[float]]:
    """
    给定问句和候选意图及其给定的例句，返回匹配到的意图

    Args:
        question (str): 问题字符串
        intent_group (dict): key为意图名称，value为该意图的例句列表

    Return:
        dict: key为意图名称，value为匹配综合相似度，范围为0-1之间
    """
    reverse_mapping = {s: k for k, v in intent_group.items() for s in v}
    corpus = list(chain(*intent_group.values()))
    corpus.append(question)

    embeddings: SemanticIndexOutputExample = semantic_index(corpus)
    question_embedding = np.array(embeddings.embeddings[0])
    corpus_embeddings = np.array(embeddings.embeddings[1:])

    # We use cosine-similarity and torch.topk to find the highest 5 scores
    cos_scores = np.inner(question_embedding, corpus_embeddings)

    k = min(len(cos_scores), 5)

    top_results = np.argpartition(cos_scores, -k)

    result = {}
    for idx in top_results:
        score = cos_scores[idx]
        intent = reverse_mapping[corpus[idx]]
        if score < 0.5:
            continue
        if intent not in result:
            result[intent] = []
        result[intent].append(score.tolist())
    return result
