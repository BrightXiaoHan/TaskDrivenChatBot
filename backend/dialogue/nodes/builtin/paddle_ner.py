import jieba
import jieba.posseg as pseg

jieba.enable_paddle()


def paddle_ner(text):
    words = pseg.cut(text, use_paddle=True)  # paddle模式
    words = filter(lambda x: x.flag == "LOC", words)
    location = "".join([item.word for item in words])
    if location:
        return {
            "@sys.loc": location,
            "@sys.gpe": location
        }
    else:
        return {}


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
