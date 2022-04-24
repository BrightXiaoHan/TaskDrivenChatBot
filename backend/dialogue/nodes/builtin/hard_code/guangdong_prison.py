"""
广东监狱项目，定制实体识别。
"""
import re
from cpca import matcher
from backend.dialogue.nodes.builtin.paddle_ner import paddle_ner


def prison(msg):
    """
    识别监狱实体
    """
    all_loc_gpe = [item.origin_value for item in matcher.iter(msg.text)]

    regex = "[一二三四五六七八九十零〇0-9]{1,4}监狱"
    ents = re.findall(regex, msg.text)

    for item in all_loc_gpe:
        regex = f"{item}[的]*监狱"
        ents += re.findall(regex, msg.text)

    if ents:
        msg.add_entities("@sys.guangdong_prison.prison", ents)

    return
    yield None


def prison_area(msg):
    """
    识别监区实体
    """
    regex = "[一二三四五六七八九十零〇0-9]{1,4}[监防]区"
    ents = re.findall(regex, msg.text)

    if ents:
        msg.add_entities("@sys.guangdong_prison.prison_area", ents)
    return
    yield None


def prison_target(msg):
    regex = "防爆队|特勤队|值班室"
    ents = re.findall(regex, msg.text)

    if ents:
        msg.add_entities("@sys.guangdong_prison.prison_target", ents)
    return
    yield None


def prison_dormitory(msg):
    """
    识别宿舍实体
    """
    regex = "[一二三四五六七八九十零〇0-9]{1,4}监狱*宿*舍"
    ents = re.findall(regex, msg.text)
    if ents:
        msg.add_entities("@sys.guangdong_prison.prison_dormitory", ents)
    return
    yield None


def floor(msg):
    """
    识别楼层实体
    """
    regex = "[一二三四五六七八九十零〇0-9]{1,4}[层楼]"
    ents = re.findall(regex, msg.text)
    if ents:
        msg.add_entities("@sys.guangdong_prison.floor", ents)
    return
    yield None


def number(msg):
    """
    识别多少多少号
    """
    regex = "[一二三四五六七八九十零〇0-9]{1,4}号"
    ents = re.findall(regex, msg.text)
    if ents:
        msg.add_entities("@sys.guangdong_prison.number", ents)
    return
    yield None


def person(msg):
    """
    识别服刑人员姓名
    """
    ents = paddle_ner(msg.text)
    if "@sys.person" in ents:
        msg.add_entities("@sys.guangdong_prison.person", ents["@sys.person"])
    return
    yield None
