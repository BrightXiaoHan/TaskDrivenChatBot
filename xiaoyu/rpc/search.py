import uuid
from itertools import chain

import ngram
import torch
from elasticsearch import helpers
from more_itertools import take
from sentence_transformers import util
from toolz import unique

from utils import (FAQ_DEFAULT_PERSPECTIVE, UNSWER_TYPE_MULTIANSWER,
                   UNSWER_TYPE_NONUSWER, UNSWER_TYPE_SINGLEANSWER)

from .manager_api import es, model

__all__ = ["search", "intent_classify", "question_clustering"]


def judge_answer(question, hits, threshold):
    """
    判断候选的问题是否符合直接返回答案的条件

    Args:
        question (str): 待匹配的问题
        hits (str): 语义匹配命中的问题
        threshold (float): 相似度的阈值

    Return
        hit: 可以作为答案的hit，没有任何命中时，返回None
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


async def query_minhash(text):
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
    robot_code,
    question,
    ans_threshold=0.5,
    rcm_threshold=0.4,
    recommend_num=5,
    perspective="",
    should_perspective="",
    use_model=True,  # 是否使用语义模型进行搜索,如果该字段为False,则使用关键字搜索
):
    response_json = {
        "answer": "",
        "match_questions": "",
        "answer_type": UNSWER_TYPE_NONUSWER,
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
                {
                    "bool": {
                        "must": [
                            {"match_phrase": {"perspective": {"query": p}}}
                            for p in perspective
                            if p  # 避免空字符串
                        ]
                    }
                },
                {
                    "bool": {
                        "should": [
                            {"match_phrase": {"perspective": {"query": p}}}
                            for p in should_perspective
                            if p  # 避免空字符串
                        ]
                    }
                },
            ]
        }
    }

    if use_model:
        question_embedding = model.encode(question)
        sem_search = await es.search(
            index=robot_code,
            body={
                "query": {
                    "script_score": {
                        "query": perspective_matcher,
                        "script": {
                            # 这里余弦相似度加1是因为score的值不能小于0
                            "source": "cosineSimilarity(params.query_vector, 'question_vector') + 1",
                            "params": {"query_vector": question_embedding},
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
        response_json["answer_type"] = UNSWER_TYPE_SINGLEANSWER
    elif answer and len(answer) > 1:
        response_json["answer"] = [item["_source"]["answer"] for item in answer]
        response_json["answer_type"] = UNSWER_TYPE_MULTIANSWER
        response_json["match_questions"] = [
            item["_source"]["question"] for item in answer
        ]
        response_json["confidence"] = [item["_score"] - 1 for item in answer]

    # 过滤掉答案相同的问题
    start = 1 if answer and len(answer) == 1 else 0
    hits = hits[start:]

    def _sim_search_filter(hit):
        if hit["_score"] - 1 < rcm_threshold:
            return False

        if (
            len(hit["_source"]["question"]) <= 4
            and ngram.NGram.compare(question, hit["_source"]["question"], N=1) == 0
        ):
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


def intent_classify(question, intent_group):
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

    corpus_embeddings = model.encode(corpus, convert_to_tensor=True)

    # We use cosine-similarity and torch.topk to find the highest 5 scores
    cos_scores = util.cos_sim(corpus_embeddings[-1], corpus_embeddings[:-1])[0]

    k = min(len(cos_scores), 5)
    top_results = torch.topk(cos_scores, k=k)

    result = {}
    for score, idx in zip(top_results[0], top_results[1]):
        intent = reverse_mapping[corpus[idx]]
        if score < 0.5:
            continue
        if intent not in result:
            result[intent] = []
        result[intent].append(score.item())

    return {"topn_score": result}


async def question_clustering(robot_code, questions, threshold=0.75):
    """
    给定一组问题，对其进行聚类，聚类结果为一个问题集合

    Args:
        question (List(str)): 问题列表，每个元素为一个问题字符串
    Return:
        List[List[int]]: 聚类结果，每个元素为一个问题的索引
    """
    corpus_embeddings = model.encode(
        questions, batch_size=32, show_progress_bar=False, convert_to_tensor=True
    )
    clusters = util.community_detection(
        corpus_embeddings, min_community_size=1, threshold=threshold, init_max_size=1
    )

    result = []
    for items in clusters:
        embs = [corpus_embeddings[i] for i in items]
        # 聚类的结果求平均值，并找出与该平均向量最接近的FAQ问题
        avg_emb = torch.mean(torch.stack(embs), dim=0).numpy()
        sem_search = await es.search(
            index=robot_code,
            body={
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            # 这里余弦相似度加1是因为score的值不能小于0
                            "source": "cosineSimilarity(params.query_vector, 'question_vector') + 1",
                            "params": {"query_vector": avg_emb},
                        },
                    }
                },
                "_source": ["question", "answer"],
                "size": 1,
                "sort": [{"_score": {"order": "desc"}}],
            },
            ignore=[400, 404],
        )
        try:
            hits = sem_search["hits"]["hits"]
            hit = hits[0]
            faq_id = hit["_id"]
            answer = hit["_source"]["answer"]
            question = hit["_source"]["question"]
            confidence = hit["_score"] - 1
        except (KeyError, IndexError):
            answer, question, confidence, faq_id = "", "", 0, ""

        result.append(
            {
                "question": question,
                "faq_id": faq_id,
                "answer": answer,
                "confidence": confidence,
                "cluster": items,
            }
        )
    return result
