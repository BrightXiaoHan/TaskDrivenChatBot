from typing import List

import fastapi
import uvicorn
from sentence_transformers import SentenceTransformer
from service_streamer import ThreadedStreamer

from interface import (
    SemanticIndexInputExample,
    SemanticIndexOutputExample,
)

app = fastapi.FastAPI()

model = SentenceTransformer("distiluse-base-multilingual-cased-v1")


def encode(texts: List[str]) -> List[List[float]]:
    return model.encode(texts, show_progress_bar=False).tolist()


streamer = ThreadedStreamer(encode, batch_size=32, max_latency=0.1)


@app.post("/xiaoyu/models/semantic-index", response_model=SemanticIndexOutputExample)
def encode(batch: SemanticIndexInputExample = fastapi.Body(...)) -> SemanticIndexOutputExample:
    vectors = streamer.predict(batch.sentences)
    return SemanticIndexOutputExample(embeddings=vectors)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8099)
