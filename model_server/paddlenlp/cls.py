from typi ng import Dict, List, Union

import fastapi
import uvicorn
from paddlenlp import Taskflow
from pydantic import BaseModel
from service_streamer import ThreadedStreamer

cls = Taskflow("zero_shot_text_classification")


class ModelInput(BaseModel):
    """
    Model input.
    Example:
        {"text_a": text_a, "text_b": "", "choices": ["这是一条差评", "这是一条好评"], "question": ""}
    """
    text_a: str
    text_b: str
    question: str
    choices: List[str]


class ModelOutput(BaseModel):
    """
    The output of the model.
    Example:
        {"predictions": [{"label": "这是一条差评", "score": 0.903727367612172}], "text_a": "东西还可以，但是快递非常慢，下次不会再买这家了。"},
    """
    text_a: str
    predictions: List[Dict[str, Union[str, float]]]


def predict(batch: List[ModelInput]) -> List[ModelOutput]:
    """
    Json example of paddle return:
    [
            ]
    """
    schema_text = [
        {"schema": ["喜事", "灾祸", "暴力倾向"], "text": ["前几天的时候，张三打了我一耳光，我想报复他", "昨天你侄子家，生了一个男孩", "昨天他开车出车祸死了"]},
        {"schema": ["开心", "伤心"], "text": ["这次考试我成绩非常不好", "这次我的成绩好极了！"]},
    ]

    batch = []
    for sub_schema_text in schema_text:
        for text_a in sub_schema_text["text"]:
            batch.append({"text_a": text_a, "text_b": "", "choices": sub_schema_text["schema"], "question": ""})

    results = []
    for example in examples:
        cls.set_schema(example.categories)
        prediction = cls(example.text)[0]
        oe = OutputExmaple(
            text=prediction["text_a"],
            label=prediction["predictions"][0]["label"],
            score=prediction["predictions"][0]["score"],
        )
        results.append(oe)
    return results


class InputExample(BaseModel):
    categories: List[str]
    text: str


class OutputExmaple(BaseModel):
    text: str
    label: str
    score: float


streamer = ThreadedStreamer(predict, batch_size=16, max_latency=0.2)
app = fastapi.FastAPI()


@app.post("/predict", response_model=OutputExmaple)
def zero_shot_text_classification(example: InputExample = fastapi.Body(..., embed=False)):
    prediction = streamer.predict([example])[0]
    return prediction


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8099)
