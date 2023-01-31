import os

import spacy

from xiaoyu.config import global_config

__all__ = ["builtin_spacy_ner"]

nlp = spacy.load(os.path.join(global_config["source_root"], "assets/zh_core_web_sm"))

ability_mapping = {
    "PERSON": "@sys.person",  # 我叫<韩冰>
    "CARDINAL": "@sys.num",  # 我有<12>个苹果
    "EVENT": "@sys.event",
    "FAC": "@sys.loc",  # 通常表示知名的纪念碑或人工制品等。
    "GPE": "@sys.gpe",  # 通常表示地理—政治条目， 我在<开封市>
    "LANGUAGE": "@sys.language",  # 你会说<英语>吗
    "LAW": "@sys.law",
    "LOC": "@sys.loc",  # LOCATION除了上述内容外，还能表示名山大川等。 我在<黄山旅游>
    "MONEY": "@sys.money",  # 给我<两块>钱
    "NORP": "@sys.norp",
    "ORDINAL": "@sys.ordinal",  # 我是<第一>名
    "ORG": "@sys.org",  # 你好我在<顺河区社保局>
    "PERCENT": "@sys.percent",  # <百分之二>的概率
    "PRODUCT": "@sys.product",
    "QUANTITY": "@sys.quantity",  # <12级>台风来了
    "WORK_OF_ART": "@sys.work_of_art",
}


def ner(text):
    doc = nlp(text)
    entites = {}
    for ent in doc.ents:
        if ent.label_ not in ability_mapping:
            continue
        key = ability_mapping[ent.label_]
        value = ent.text
        if key not in entites:
            entites[key] = [value]
        else:
            entites[key].append(value)
    return entites


def builtin_spacy_ner(msg):
    entities = ner(msg.text)
    for key, value in entities.items():
        msg.add_entities(key, value)
    return iter(())


if __name__ == "__main__":
    while True:
        text = input("请输入待识别的文字: ")
        print(ner(text))
