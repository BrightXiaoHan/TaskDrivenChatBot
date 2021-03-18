"""
项目帮助函数
"""
import time
import json

from hashlib import blake2b
import requests

from utils.exceptions import RpcException


__all__ = ["hash_string", "get_time_stamp"]


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


def post_rpc(url, data):
    """
    给定url和调用参数，通过http post请求进行rpc调用
    """
    try:
        response = requests.post(url, json=data, timeout=3)
        response_data = json.loads(response.text)
    except requests.Timeout as exp:
        raise RpcException(url, data, "服务请求超时")

    return response_data
