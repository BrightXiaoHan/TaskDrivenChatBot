import jieba
import jieba.posseg as pseg

jieba.enable_paddle()


def paddle_ner(text):
    ents = {}

    words = list(pseg.cut(text, use_paddle=True))  # paddle模式
    loc_words = filter(lambda x: x.flag == "LOC", words)
    location = "".join([item.word for item in loc_words])
    if location:
        ents.update({"@sys.loc": location, "@sys.gpe": location})

    person_words = filter(lambda x: x.flag == "PER", words)
    person = "".join([item.word for item in person_words])
    if person:
        ents.update({"@sys.person": person})

    return ents


def builtin_paddle_ner(msg):
    entities = paddle_ner(msg.text)
    for key, value in entities.items():
        msg.add_entities(key, value)
    return
    yield None


if __name__ == "__main__":
    while True:
        text = input("请输入待识别的文字: ")
        print(paddle_ner(text))
