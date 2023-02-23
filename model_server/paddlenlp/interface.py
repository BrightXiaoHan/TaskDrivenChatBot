from typing import Dict, List

from pydantic import BaseModel


class CompareInputExample(BaseModel):
    text_a: str
    text_b: str


class CompareOutputExample(BaseModel):
    text_a: str
    text_b: str
    label: str
    score: float


class SentimentAnalysisInputExample(BaseModel):
    text: str
    categories: List[str] = ["正面", "负面"]


class SentimentAnalysisOutputExmaple(BaseModel):
    text: str
    label: str
    score: float


class ClassificationInputExample(BaseModel):
    categories: List[str]
    text: str


class ClassificationOutputExmaple(BaseModel):
    text: str
    label: str
    score: float
    no_label: bool = False


class InformationExtractionInputExample(BaseModel):
    categories: List[str]
    text: str


class InformationExtractionOutputExample(BaseModel):
    class ModelOutput(BaseModel):
        text: str
        start: int
        end: int
        probablity: float
        type: str

    text: str
    entities: List[ModelOutput]


class NERInputExample(BaseModel):
    text: str


class NEROutputExample(BaseModel):
    class ModelOutput(BaseModel):
        text: str
        start: int
        end: int

    text: str
    entities: Dict[str, List[ModelOutput]]


class QAInputExample(BaseModel):
    text: str


class QAOutputExample(BaseModel):
    text: str
    answer: str


class DialogueInputExample(BaseModel):
    text: str


class DialogueOutputExample(BaseModel):
    text: str
    answer: str
