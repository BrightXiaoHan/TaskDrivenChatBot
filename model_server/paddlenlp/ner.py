from typing import List, Tuple

import fastapi
import uvicorn
from interface import NERInputExample, NEROutputExample
from paddlenlp import Taskflow
from pydantic import BaseModel
from service_streamer import ThreadedStreamer


class ModelInput(BaseModel):
    text: str


class ModelOutput(BaseModel):
    nes: List[Tuple[str, str]]


ner = Taskflow("ner", entity_only=True)


"""
Example output from ie([text] * 2):
[
    [
        ("热梅茶", "饮食类_饮品"),
        ("是", "肯定词"),
        ("一道", "数量词"),
        ("以", "介词"),
        ("梅子", "饮食类"),
        ("为", "肯定词"),
        ("主要原料", "物体类"),
        ("制作", "场景事件"),
        ("的", "助词"),
        ("茶饮", "饮食类_饮品"),
    ],
    [
        ("《", "w"),
        ("孤女", "作品类_实体"),
        ("》", "w"),
        ("是", "肯定词"),
        ("2010年", "时间类"),
        ("九州出版社", "组织机构类"),
        ("出版", "场景事件"),
        ("的", "助词"),
        ("小说", "作品类_概念"),
        ("，", "w"),
        ("作者", "人物类_概念"),
        ("是", "肯定词"),
        ("余兼羽", "人物类_实体"),
    ],
]
"""


def predict(batch: List[ModelInput]) -> List[ModelOutput]:
    texts = [item.text for item in batch]
    result = ner(texts)
    if len(texts) == 1:
        result = [result]
    return [ModelOutput(nes=item) for item in result]


streamer = ThreadedStreamer(predict, batch_size=32, max_latency=0.1)


app = fastapi.FastAPI()


@app.post("/xiaoyu/models/ner", response_model=NEROutputExample)
def information_extraction(input: NERInputExample = fastapi.Body(...)):
    example = ModelInput(text=input.text)
    prediction = streamer.predict([example])[0]
    entities = {}

    for entity, label in prediction.nes:
        if label not in entities:
            entities[label] = []
        entities[label].append(
            NEROutputExample.ModelOutput(
                text=entity,
                start=input.text.find(entity),
                end=input.text.find(entity) + len(entity),
            )
        )

    return NEROutputExample(
        text=input.text,
        entities=entities,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8099)
