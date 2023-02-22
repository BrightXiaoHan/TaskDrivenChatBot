from typing import List, Union

from pydantic import BaseModel


class SemanticIndexInputExample(BaseModel):
    sentences: Union[List[str], str]


class SemanticIndexOutputExample(BaseModel):
    embeddings: Union[List[List[float]], List[float]]
