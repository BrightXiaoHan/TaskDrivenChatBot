from typing import List

import fastapi
import uvicorn
from paddlenlp import Taskflow
from pydantic import BaseModel
from service_streamer import ThreadedStreamer

from interface import (
    InformationExtractionInputExample,
    InformationExtractionOutputExample,
)


class ModelInput(BaseModel):
    categories: List[str]
    text: str


class ModelOutput(BaseModel):
    text: str
    start: int
    end: int
    probablity: float
    type: str


ie = Taskflow("information_extraction")

"""
Example output from ie([text] * 2):
[
    {
        "时间": [{"text": "2021年8月8日", "start": 0, "end": 9, "probability": 0.9748135873973851}],
        "赛事名称": [{"text": "2021年世界排球锦标赛中国区预选赛", "start": 15, "end": 33, "probability": 0.885254118626861}],
    },
    {
        "时间": [{"text": "2021年8月8日", "start": 0, "end": 9, "probability": 0.9748135873973851}],
        "赛事名称": [{"text": "2021年世界排球锦标赛中国区预选赛", "start": 15, "end": 33, "probability": 0.8852540054733353}],
    },
]
"""


def predict(batch: List[ModelInput]) -> List[ModelOutput]:
    """ """
    results = []
    for item in batch:
        ie.set_schema(item.categories)
        prediction = ie(item.text)[0]
        nes = []
        for k, v in prediction.items():
            for i in v:
                nes.append(
                    ModelOutput(
                        text=i["text"],
                        start=i["start"],
                        end=i["end"],
                        probablity=i["probability"],
                        type=k,
                    )
                )
        results.append(nes)
    return results


streamer = ThreadedStreamer(predict, batch_size=8, max_latency=0.1)


app = fastapi.FastAPI()


@app.post("/xiaoyu/models/information-extraction", response_model=InformationExtractionOutputExample)
def information_extraction(input: InformationExtractionInputExample = fastapi.Body(...)):
    example = ModelInput(categories=input.categories, text=input.text)
    prediction = streamer.predict([example])[0]
    response = InformationExtractionOutputExample(text=input.text, entities=prediction)
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8099)
