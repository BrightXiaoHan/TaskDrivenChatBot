from typing import List

import fastapi
import uvicorn
from interface import QAInputExample, QAOutputExample
from paddlenlp import Taskflow
from pydantic import BaseModel
from service_streamer import ThreadedStreamer


class ModelInput(BaseModel):
    text: str


class ModelOutput(BaseModel):
    text: str
    answer: str


qa = Taskflow("question_answering")


"""
Example output from ie([text] * 2):
[{"text": "中国国土面积有多大？", "answer": "960万平方公里。"}, {"text": "中国的首都在哪里？", "answer": "北京。"}]
"""


def predict(batch: List[ModelInput]) -> List[ModelOutput]:
    texts = [item.text for item in batch]
    result = qa(texts)
    return [ModelOutput(text=item["text"], answer=item["answer"]) for item in result]


streamer = ThreadedStreamer(predict, batch_size=32, max_latency=0.1)


app = fastapi.FastAPI()


@app.post("/xiaoyu/models/question-answering", response_model=QAOutputExample)
def information_extraction(input: QAInputExample = fastapi.Body(...)):
    batch = [ModelInput(text=input.text)]
    output = streamer.predict(batch)[0]
    return QAOutputExample(text=output.text, answer=output.answer)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8099)
