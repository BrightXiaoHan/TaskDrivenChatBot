from typing import List

from pydantic import BaseModel


class SemanticIndexInputExample(BaseModel):
    sentences: List[str]


class SemanticIndexOutputExample(BaseModel):
    embeddings: List[List[float]]
