from typing import List

import fastapi
import uvicorn
from interface import DialogueInputExample, DialogueOutputExample
from paddlenlp import Taskflow
from pydantic import BaseModel
from service_streamer import ThreadedStreamer


class ModelInput(BaseModel):
    text: str


class ModelOutput(BaseModel):
    text: str
    answer: str


dialogue = Taskflow("dialogue")


"""
Example output from ie([text] * 2):
['吃过了,你呢', '我是李明啊']
"""


def predict(batch: List[ModelInput]) -> List[ModelOutput]:
    texts = [item.text for item in batch]
    result = dialogue(texts)
    return [ModelOutput(text=text, answer=item) for text, item in zip(texts, result)]


streamer = ThreadedStreamer(predict, batch_size=32, max_latency=0.1)


app = fastapi.FastAPI()


@app.post("/xiaoyu/models/dialogue", response_model=DialogueOutputExample)
def information_extraction(input: DialogueInputExample = fastapi.Body(...)):
    batch = [ModelInput(text=input.text)]
    output = streamer.predict(batch)[0]
    return DialogueOutputExample(text=output.text, answer=output.answer)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8099)
