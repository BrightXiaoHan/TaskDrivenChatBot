import spacy
from pyunit_time import Time

__all__ = ["ner"]

nlp = spacy.load("zh_core_web_sm")

ability_mapping = {
    "PERSON": "@sys.person",  # 我叫<韩冰>
    'CARDINAL': "@sys.num",  # 我有<12>个苹果
    'DATE': "@sys.date",  # 今天<星期天>
    'EVENT': "@sys.event",
    'FAC': "@sys.loc",  # 通常表示知名的纪念碑或人工制品等。
    'GPE': "@sys.gpe",  # 通常表示地理—政治条目， 我在<开封市>
    'LANGUAGE': "@sys.language",  # 你会说<英语>吗
    'LAW': "@sys.law",
    'LOC': "@sys.loc",  # LOCATION除了上述内容外，还能表示名山大川等。 我在<黄山旅游>
    'MONEY': "@sys.money",  # 给我<两块>钱
    'NORP': "@sys.norp",
    'ORDINAL': "@sys.ordinal",  # 我是<第一>名
    'ORG': "@sys.org",  # 你好我在<顺河区社保局>
    'PERCENT': "@sys.percent",  # <百分之二>的概率
    'PRODUCT': "@sys.product",
    'QUANTITY': "@sys.quantity",  # <12级>台风来了
    'TIME': "@sys.time",  # 现在是<11点三十分>
    'WORK_OF_ART': "@sys.work_of_art"
}


def normalize(key, value):
    """将识别到的实体进行标准化处理

    Args:
        key (str): 实体类别
        value (str): 实体值
    """
    if key == "@sys.time":
        result = Time().parse(value)
        if len(result) == 0:
            return value
        key_time = result[0]["keyDate"].split()[1]
        base_time = result[0]["baseDate"].split()[1]
        result_time = key_time.split(":")[0]
        for t1, t2 in zip(key_time.split(":")[1:], base_time.split(":")[1:]):
            if t1 == t2:
                result_time += ":00"
            else:
                result_time += ":" + t1
        return result_time

    elif key == "@sys.date":
        result = Time().parse(value)
        if len(result) == 0:
            return value
        value = result[0]["keyDate"].split()[0]
        return value
    else:
        return value


def ner(text):
    doc = nlp(text)
    entites = {}
    for ent in doc.ents:
        key = ability_mapping[ent.label_]
        value = ent.text
        value = normalize(key, value)
        if key not in entites:
            entites[key] = [value]
        else:
            entites[key].append(value)
    return entites


if __name__ == "__main__":
    print(ner("明天上午六点"))
