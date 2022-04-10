"""
项目帮助函数
"""
import time
import json
import uuid

from hashlib import blake2b
from strsimpy.levenshtein import Levenshtein

import requests
import aiohttp

from utils.exceptions import RpcException


__all__ = ["hash_string", "get_time_stamp", "post_rpc", "generate_uuid"]

levenshtein = Levenshtein()

def levenshtein_sim(query, candidates):
    """
    计算candidate中与query编辑距离最小的值， 返回最小距离和匹配结果

    Args:
        query (str): 待匹配的文本，一般是用户说的话
        candidates (List[str]): 候选文本，一般是选项文本
    
    Return:
        str: candidates中与query编辑距离最小的文本
        int: 编辑距离值
    """
    distances = [levenshtein.distance(query, c) for c in candidates ]
    distance = min(distances)
    candidate = candidates[distances.index(distance)]
    return candidate, distance


def generate_uuid():
    return "".join(str(uuid.uuid1()).split("-")).upper()


def hash_string(content, size=20):
    """使用hashlib对一段文本内容生成hash值

    Args:
        content (str): 待hash的字符串内容
        size (str): hash值的长度

    Return:
        str: 字符串的hash结果
    """
    h = blake2b(digest_size=size)
    h.update(content)
    return h.hexdigest()


def get_time_stamp():
    """
    获取当前时间的时间戳

    Return:
        str: 格式为'%Y-%m-%d %H:%M:%S', 如"2021-2-10 10:00:00"

    """
    return time.strftime('%Y-%m-%d %H:%M:%S')


def post_rpc(url, data, data_type="json", **kwargs):
    """
    给定url和调用参数，通过http post请求进行rpc调用

    Args:
        url (str): 调用请求的url地址
        data (str): 调用接口的
        data_type (str, optional): json 或者 params
    """
    try:
        if data_type == "json":
            response = requests.post(url, json=data, timeout=10, **kwargs)
        else:
            response = requests.post(url, data=data, timeout=10, **kwargs)
        response_data = json.loads(response.text)
    except requests.Timeout:
        raise RpcException(url, data, "服务请求超时")
    except json.JSONDecodeError:
        raise RpcException(url, data, response.text)

    return response_data


def get_rpc(url, params, **kwargs):
    """给定url和调用参数，通过http get请求进行rpc调用

    Args:
        url (str): 调用请求的url地址
        params (str): 调用接口的
    """
    try:
        response = requests.get(url, params=params, timeout=3, **kwargs)
        response_data = json.loads(response.text)
    except requests.Timeout:
        raise RpcException(url, params, "服务请求超时")
    except json.JSONDecodeError:
        raise RpcException(url, params, "服务返回值json解析失败")

    return response_data

async def async_post_rpc(url, data, data_type="json", **kwargs):
    """
    给定url和调用参数，通过http post请求进行rpc调用。
    post_rpc函数的异步版本

    Args:
        url (str): 调用请求的url地址
        data (str): 调用接口的
        data_type (str, optional): json 或者 params
    """
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            response = await session.post(url, json=data, **kwargs)
            response_data = json.loads(await response.text())
        
    except aiohttp.ClientError:
        raise RpcException(url, data, "服务请求超时")
    except json.JSONDecodeError:
        raise RpcException(url, data, response.text())

    return response_data

async def async_get_rpc(url, params, **kwargs):
    """给定url和调用参数，通过http get请求进行rpc调用。

    Args:
        url (str): 调用请求的url地址
        params (str): 调用接口的
    """
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
            response = await session.get(url, params=params, **kwargs)
            response_data = json.loads(await response.text())
    except aiohttp.ClientError:
        raise RpcException(url, params, "服务请求超时")
    except json.JSONDecodeError:
        raise RpcException(url, params, "服务返回值json解析失败")

    return response_data