import aiohttp

from .paddlenlp import (
    ClassificationInputExample,
    ClassificationOutputExmaple,
    CompareInputExample,
    CompareOutputExample,
    InformationExtractionInputExample,
    InformationExtractionOutputExample,
    SentimentAnalysisInputExample,
    SentimentAnalysisOutputExmaple,
)
from .sentence_transformers import SemanticIndexInputExample, SemanticIndexOutputExample


async def classification(input: ClassificationInputExample) -> ClassificationOutputExmaple:
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:8000/classification", json=input.dict()) as response:
            return ClassificationOutputExmaple(**await response.json())


async def compare(input: CompareInputExample) -> CompareOutputExample:
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:8000/compare", json=input.dict()) as response:
            return CompareOutputExample(**await response.json())


async def sentiment_analysis(input: SentimentAnalysisInputExample) -> SentimentAnalysisOutputExmaple:
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:8000/sentiment_analysis", json=input.dict()) as response:
            return SentimentAnalysisOutputExmaple(**await response.json())


async def information_extraction(input: InformationExtractionInputExample) -> InformationExtractionOutputExample:
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:8000/information_extraction", json=input.dict()) as response:
            return InformationExtractionOutputExample(**await response.json())


async def semantic_index(input: SemanticIndexInputExample) -> SemanticIndexOutputExample:
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:8000/semantic_index", json=input.dict()) as response:
            return SemanticIndexOutputExample(**await response.json())
