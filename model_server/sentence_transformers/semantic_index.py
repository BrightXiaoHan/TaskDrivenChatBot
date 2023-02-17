from typing import List

import fastapi
import uvicorn
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from service_streamer import ThreadedStreamer

app = fastapi.FastAPI()

model = SentenceTransformer("distiluse-base-multilingual-cased-v1")


def encode(texts: List[str]) -> List[List[float]]:
    return model.encode(texts, show_progress_bar=False).tolist()


streamer = ThreadedStreamer(encode, batch_size=32, max_latency=0.1)


class RequestBody(BaseModel):
    sentences: List[str]


class ResponseBody(BaseModel):
    embeddings: List[List[float]]


@app.post("/xiaoyu/models/semantic-index", response_model=ResponseBody)
def encode(batch: RequestBody = fastapi.Body(...)) -> ResponseBody:
    vectors = streamer.predict(batch.sentences)
    return ResponseBody(embeddings=vectors)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8099)
