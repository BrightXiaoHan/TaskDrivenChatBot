from paddlenlp import Taskflow
from pydantic import BaseModel

ie = Taskflow("information_extraction")


class ModelInput(BaseModel):
    text: str


class ModelOutput(BaseModel):
    text: str
    start: int
    end: int
    probablity: float
