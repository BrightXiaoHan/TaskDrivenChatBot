from typing import Dict, List, Union

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
    text_b: str = ""
    predictions: List[Dict[str, Union[str, float]]]


def predict(batch: List[ModelInput]) -> List[ModelOutput]:
    output = cls([item.dict() for item in batch])
    return [ModelOutput(**o) for o in output]


streamer = ThreadedStreamer(predict, batch_size=16, max_latency=0.2)
app = fastapi.FastAPI()


class ClassificationInputExample(BaseModel):
    categories: List[str]
    text: str


class ClassificationOutputExmaple(BaseModel):
    text: str
    label: str
    score: float
    no_label: bool = False


@app.post("/xiaoyu/models/classification", response_model=ClassificationOutputExmaple)
def classification(example: ClassificationInputExample = fastapi.Body(..., embed=False)):
    example = ModelInput(
        text_a=example.text,
        text_b="",
        question="",
        choices=example.categories,
    )
    prediction: List[ModelOutput] = streamer.predict([example])
    if len(prediction) == 0:
        return ClassificationOutputExmaple(text=example.text, label="", score=0.0, no_label=True)
    else:
        prediction = prediction[0]
        result = ClassificationOutputExmaple(
            text=prediction.text_a,
            label=prediction.predictions[0]["label"],
            score=prediction.predictions[0]["score"],
        )
        return result


class SentimentAnalysisInputExample(BaseModel):
    text: str
    categories: List[str] = ["正面", "负面"]


class SentimentAnalysisOutputExmaple(BaseModel):
    text: str
    label: str
    score: float


@app.post("/xiaoyu/models/sentiment-analysis", response_model=SentimentAnalysisOutputExmaple)
def sentiment_analysis(example: SentimentAnalysisInputExample = fastapi.Body(..., embed=False)):
    example = ModelInput(
        text_a=example.text,
        text_b="",
        question="",
        choices=example.categories,
    )
    prediction: List[ModelOutput] = streamer.predict([example])
    if len(prediction) == 0:
        prediction = prediction[0]
        result = SentimentAnalysisInputExample(
            text=prediction.text_a,
            label=prediction.predictions[0]["label"],
            score=prediction.predictions[0]["score"],
        )
        return result
    else:
        return SentimentAnalysisOutputExmaple(text=example.text_a, label="中性", score=0.0)


class CompareInputExample(BaseModel):
    text_a: str
    text_b: str


class CompareOutputExample(BaseModel):
    text_a: str
    text_b: str
    label: str
    score: float


@app.post("/xiaoyu/models/compare", response_model=CompareOutputExample)
def compare(example: CompareInputExample = fastapi.Body(..., embed=False)):
    example = ModelInput(
        text_a=example.text_a,
        text_b=example.text_b,
        question="",
        choices=["相同", "不同"],
    )
    prediction: List[ModelOutput] = streamer.predict([example])
    if len(prediction) == 0:
        return CompareOutputExample(text_a=example.text_a, text_b=example.text_b, label="不相关", score=0.0)
    else:
        prediction = prediction[0]
        result = CompareOutputExample(
            text_a=prediction.text_a,
            text_b=prediction.text_b,
            label=prediction.predictions[0]["label"],
            score=prediction.predictions[0]["score"],
        )
        return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8099)
