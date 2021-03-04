"""
项目帮助函数
"""
from hashlib import blake2b

__all__ = ["hash_string"]


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
