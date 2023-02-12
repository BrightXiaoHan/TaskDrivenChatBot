from elasticsearch import AsyncElasticsearch, helpers
from more_itertools import chunked
from sentence_transformers import SentenceTransformer

from config import global_config
from utils import FAQ_DEFAULT_PERSPECTIVE

__all__ = [
    "upload_documents",
    "delete_documents",
    "delete_robot",
    "create_robot",
    "copy",
]

# 创建训练进程
es = AsyncElasticsearch([global_config["elasticsearch_url"]])
model = SentenceTransformer("assets/semantic_model")

es_index = {
    "mappings": {
        "properties": {
            "question_vector": {"type": "dense_vector", "dims": 512},
            "question": {"type": "text", "copy_to": "minhash_value"},
            "answer": {"type": "text"},
            "perspective": {"type": "text"},
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


async def upload_documents(robot_code, documents, use_model=True):
    if not await es.indices.exists(index=robot_code):
        await es.indices.create(index=robot_code, body=es_index)
    bulk_data = []
    for batch in chunked(documents, 10):
        questions = [item["question"] for item in batch]
        if use_model:
            embeddings = model.encode(questions, show_progress_bar=False)
            for item, embedding in zip(batch, embeddings):
                bulk_data.append(
                    {
                        "_index": robot_code,
                        "_id": item["id"],
                        "_source": {
                            "question": item["question"],
                            "question_vector": embedding,
                            "answer": item["answer"],
                            "perspective": item.get(
                                "perspective", FAQ_DEFAULT_PERSPECTIVE
                            ),
                        },
                    }
                )
        else:
            for item in batch:
                bulk_data.append(
                    {
                        "_index": robot_code,
                        "_id": item["id"],
                        "_source": {
                            "question": item["question"],
                            "answer": item["answer"],
                            "perspective": item.get(
                                "perspective", FAQ_DEFAULT_PERSPECTIVE
                            ),
                        },
                    }
                )
    await helpers.async_bulk(es, bulk_data, refresh=True)
    return {"status_code": 0}


async def delete_documents(robot_code, q_ids):
    if await es.indices.exists(index=robot_code):
        query = {"query": {"terms": {"_id": q_ids}}}
        await es.delete_by_query(index=robot_code, body=query, refresh=True)
    return {"status_code": 0}


async def delete_robot(robot_code):
    await es.indices.delete(index=robot_code, ignore=[400, 404])
    return {"status_code": 0}


async def create_robot(robot_code):
    # 创建机器人没有什么要做的，索引创建与上传文档会进行合并
    return {"status_code": 0}


async def copy(robot_code: str, target_robot_code: str, refresh=False) -> dict:
    """
    将faq语料库从机器人`robot_code`中复制到`target_robot_code`中
    """
    # 如果原有机器人存在，则删除原有机器人
    delete_robot(target_robot_code)
    if not await es.indices.exists(index=target_robot_code):
        await es.indices.create(index=target_robot_code, body=es_index, ignore=[400])
    query = {"source": {"index": robot_code}, "dest": {"index": target_robot_code}}
    await es.reindex(query, ignore=[400, 404], refresh=refresh)
    return {"status_code": 0}

